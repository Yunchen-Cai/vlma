package nusri.fyp.demo.service.img_sender;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import nusri.fyp.demo.dto.NodeRuntimeSnapshot;
import nusri.fyp.demo.repository.PythonServerRepository;
import nusri.fyp.demo.service.ConfigService;
import nusri.fyp.demo.service.img_sender.python.ImageSenderOfPython;
import nusri.fyp.demo.service.img_sender.roboflow.ImageSenderOfRoboflow;
import nusri.fyp.demo.service.img_sender.roboflow.RoboflowService;
import nusri.fyp.demo.state_machine.AbstractActionObservation;
import nusri.fyp.demo.state_machine.StateMachine;
import org.opencv.core.Mat;
import org.opencv.videoio.VideoCapture;
import org.opencv.videoio.Videoio;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.*;

@Service
@Slf4j
public class ImageSenderService {

    private final ConfigService configService;
    public final Map<String, File> tempFiles = new ConcurrentHashMap<>();
    public final Map<String, Long> totleFramesMap = new ConcurrentHashMap<>();
    public final Map<String, Map<Long, List<? extends AbstractActionObservation>>> progressMap = new ConcurrentHashMap<>();
    public final Map<String, List<CompletableFuture<List<AbstractActionObservation>>>> sendingProcesses = new ConcurrentHashMap<>();
    private final RoboflowService roboflowService;

    private final ImageSenderOfRoboflow imageSenderOfRoboflow;
    private final ImageSenderOfPython imageSenderOfPython;

    public ImageSenderService(ConfigService configService,
                              RoboflowService roboflowService,
                              ObjectMapper objectMapper,
                              PythonServerRepository pythonServerRepository) {
        this.configService = configService;
        this.imageSenderOfRoboflow = new ImageSenderOfRoboflow(roboflowService);
        this.imageSenderOfPython = new ImageSenderOfPython(this, objectMapper, pythonServerRepository);
        this.roboflowService = roboflowService;
    }

    // 关键修改：
    // 1) 增加 StateMachine 参数
    // 2) 改成逐帧顺序发送
    // 3) 每帧发送前动态计算 expectedCondition
    // 4) 每帧收到结果后立刻更新状态机
    public Map<Long, List<? extends AbstractActionObservation>> sendVideoFile(
            File file,
            String user,
            Map<String, String> config,
            ImageSender imageSender,
            StateMachine stateMachine
    ) throws IOException {
        File dir = new File(configService.getVideoPath());
        if (!dir.exists()) {
            //noinspection ResultOfMethodCallIgnored
            dir.mkdirs();
        }

        String absolutePath = file.getAbsolutePath();
        log.info("Reading video file at: {}", absolutePath);
        VideoCapture videoCapture = new VideoCapture(absolutePath);

        if (!videoCapture.isOpened()) {
            throw new IOException("Error opening video file");
        }

        Mat frame = new Mat();
        Map<Long, List<? extends AbstractActionObservation>> observations = new TreeMap<>();

        int jump = Integer.parseInt(configService.getFrameInterval());

        long totalFrames = (long) videoCapture.get(Videoio.CAP_PROP_FRAME_COUNT) / jump;
        totleFramesMap.put(user, totalFrames);
        log.info("Total frames: {}", totalFrames);

        progressMap.put(user, observations);

        int filter = 0;
        long frameIndex = 0;
        double fps = videoCapture.get(Videoio.CAP_PROP_FPS);
        if (fps <= 0) {
            fps = 30.0;
        }
        log.info("fps: {}", fps);

        try {
            while (videoCapture.read(frame)) {
                if (Thread.currentThread().isInterrupted()) {
                    throw new IOException("Interrupted by user");
                }

                if (frame.empty()) {
                    break;
                }

                filter++;
                if (filter % jump != 0) {
                    continue;
                }

                Mat clonedFrame = new Mat();
                frame.copyTo(clonedFrame);

                try {
                    long frameTimestamp = (long) (frameIndex * 1000 * jump / fps);

                    Map<String, String> frameConfig = new HashMap<>(config);
                    String expectedCondition = resolveExpectedCondition(stateMachine);
                    if (expectedCondition != null && !expectedCondition.isBlank()) {
                        frameConfig.put("expectedCondition", expectedCondition);
                    }

                    log.info("frameIndex={}, timestamp={}, expectedCondition={}",
                            frameIndex, frameTimestamp, expectedCondition);

                    List<? extends AbstractActionObservation> actionObs =
                            imageSender.sendFrame(clonedFrame, frameConfig);

                    observations.put(frameTimestamp, actionObs);

                    List<AbstractActionObservation> typedList =
                            actionObs.stream().map(o -> (AbstractActionObservation) o).toList();

                    stateMachine.getObservations().put(frameTimestamp, typedList);
                    stateMachine.updateStateProbability(typedList, (double) frameTimestamp);

                    frameIndex++;
                } finally {
                    clonedFrame.release();
                }
            }
        } finally {
            videoCapture.release();
            frame.release();
        }

        return observations;
    }

    private String resolveExpectedCondition(StateMachine stateMachine) {
        try {
            if (stateMachine == null || stateMachine.getSnapshot() == null) {
                return null;
            }

            NodeRuntimeSnapshot next = stateMachine.getMostProbableNextStateSnapshot();

            if (next == null) {
                return null;
            }

            return next.condition();
        } catch (Exception e) {
            log.warn("Failed to resolve expected condition: {}", e.getMessage());
            return null;
        }
    }

    public void processImg(String img,
                           String timestamp,
                           StateMachine stateMachine,
                           Map<String, String> config) {
        ImageSender imageSender = getUseImageSender(stateMachine.getSnapshot().presetName());

        List<? extends AbstractActionObservation> actionObservations = imageSender.sendFrame(img, config);

        Map<Long, List<AbstractActionObservation>> existingObs = stateMachine.getObservations();

        List<AbstractActionObservation> typedList =
                actionObservations.stream().map(o -> (AbstractActionObservation) o).toList();

        long timeKey = (long) Double.parseDouble(timestamp);
        existingObs.put(timeKey, typedList);

        stateMachine.setObservations(existingObs);
        stateMachine.updateStateProbability(typedList, Double.parseDouble(timestamp));
    }

    public ImageSender getUseImageSender(String presetName) {
        return configService.getUseModel(presetName).startsWith("python")
                ? imageSenderOfPython
                : imageSenderOfRoboflow;
    }

    public void interrupt(String user) {
        imageSenderOfRoboflow.interrupt(user);
        imageSenderOfPython.interrupt(user);
    }

    public void testRoboflow(String host, String port) throws ExecutionException, InterruptedException {
        roboflowService.test(host, port);
    }
}
