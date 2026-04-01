package nusri.fyp.demo.service;

import lombok.extern.slf4j.Slf4j;
import nusri.fyp.demo.entity.PresetNode;
import nusri.fyp.demo.entity.QuotaConfig;
import nusri.fyp.demo.repository.RoboflowWorkflowRepository;
import nusri.fyp.demo.service.img_sender.ImageSender;
import nusri.fyp.demo.service.img_sender.ImageSenderService;
import nusri.fyp.demo.service.img_sender.python.ImageSenderOfPython;
import nusri.fyp.demo.service.img_sender.roboflow.ImageSenderOfRoboflow;
import nusri.fyp.demo.state_machine.AbstractActionObservation;
import nusri.fyp.demo.state_machine.StateMachine;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.*;
import java.net.MalformedURLException;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;

@Service
@Slf4j
public class VideoService {

    private final ConfigService configService;
    private final StateMachineService stateMachineService;
    private final RoboflowWorkflowRepository roboflowWorkflowRepository;
    private final ImageSenderService imageSenderService;

    public VideoService(ConfigService configService,
                        StateMachineService stateMachineService,
                        RoboflowWorkflowRepository roboflowWorkflowRepository,
                        ImageSenderService imageSenderService) {
        this.configService = configService;
        this.stateMachineService = stateMachineService;
        this.roboflowWorkflowRepository = roboflowWorkflowRepository;
        this.imageSenderService = imageSenderService;
    }

    public ResponseEntity<?> processVideo(String user, String presetName) {
        log.info("user start to process video: {}", user);
        String modelWithConfig = configService.getUseModel(presetName);
        Map<String, String> config = buildConfig(modelWithConfig);

        if (!imageSenderService.tempFiles.containsKey(user)) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("No file uploaded");
        }

        // 关键修改：
        // 1) 先启动状态机
        // 2) 给 sendVideoFile 逐帧顺序处理时使用
        stateMachineService.start(user, presetName);
        StateMachine stateMachine = stateMachineService.getStateMachineByName(user);
        stateMachine.setObservations(new TreeMap<>());

        AtomicReference<Map<Long, List<AbstractActionObservation>>> observations = new AtomicReference<>();
        Thread thread = new Thread(() -> {
            try {
                Map<Long, List<? extends AbstractActionObservation>> longListMap =
                        imageSenderService.sendVideoFile(
                                imageSenderService.tempFiles.get(user),
                                user,
                                config,
                                imageSenderService.getUseImageSender(presetName),
                                stateMachine
                        );

                Map<Long, List<AbstractActionObservation>> listMap = new TreeMap<>();
                longListMap.forEach((key, value) ->
                        listMap.put(key, value.stream().map(a -> (AbstractActionObservation) a).toList())
                );
                observations.set(listMap);

            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        });

        log.info("user start to process video- thread.start();: {}", user);
        thread.start();
        stateMachineService.addProcess(user, thread);

        try {
            thread.join();

            if (observations.get() == null || observations.get().isEmpty()) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error processing video");
            }

            // 不要在这里再次 start，否则会把逐帧更新好的状态机重置掉
            stateMachine.setObservations(observations.get());

            log.info("user start to process video- return ResponseEntity.ok(observations.get());: {}", user);
            return ResponseEntity.ok(observations.get());
        } catch (InterruptedException | NullPointerException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Interrupted by user");
        }
    }

    public ResponseEntity<String> uploadAndSave(MultipartFile videoFile, String user) throws IOException {
        stateMachineService.stopStateMachine(user);
        imageSenderService.interrupt(user);

        if (videoFile.isEmpty()) {
            log.error("video file is empty");
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("No file uploaded");
        }

        String destinationPath = configService.getVideoPath() + File.separator + user + ".mp4";
        if (!isValidFilename(user)) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Invalid video file name");
        }

        File destinationFile = new File(destinationPath);
        try (BufferedOutputStream stream = new BufferedOutputStream(new FileOutputStream(destinationFile))) {
            stream.write(videoFile.getBytes());
            stream.flush();
        }
        log.info("Saved video file to {}", destinationFile.getAbsolutePath());

        imageSenderService.tempFiles.put(user, destinationFile);
        return null;
    }

    public static boolean isValidFilename(String name) {
        if (name == null || name.trim().isEmpty()) {
            log.error("Invalid video file name: name is null or empty");
            return false;
        }

        String invalidChars = "[\\\\/:*?\"<>|]";
        if (name.matches(".*" + invalidChars + ".*")) {
            log.error("Invalid video file name: name contains invalid characters");
            return false;
        }

        String[] reservedNames = {
                "CON", "PRN", "AUX", "NUL",
                "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
                "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        };
        for (String reserved : reservedNames) {
            if (name.equalsIgnoreCase(reserved)) {
                log.error("Invalid video file name: name contains invalid characters: '{}'", reserved);
                return false;
            }
        }
        return true;
    }

    public boolean processImage(String img, String user, String timestamp) {
        if (img.isEmpty()) {
            return false;
        }

        StateMachine stateMachineByName = stateMachineService.getStateMachineByName(user);
        String presetName = stateMachineByName.getSnapshot().presetName();
        String modelWithConfig = configService.getUseModel(presetName);
        QuotaConfig quotaConfig = stateMachineByName.getQuotaConfig();
        Map<String, String> config = buildConfig(modelWithConfig);

        PresetNode mostProbableNextState = stateMachineByName.getMostProbableNextState();
        List<String> actions = mostProbableNextState.getActions();

        List<String> expectedTools = new ArrayList<>();
        List<String> expectedActions = new ArrayList<>();

        for (String s : actions) {
            if (s == null) continue;
            String t = s.trim();
            if (t.isEmpty()) continue;

            String[] parts = t.split("_", 4);
            if (parts.length < 3) continue;

            expectedActions.add(parts[0]);
            expectedTools.add(parts[2]);
        }

        config.put("expectedTool", expectedTools.toString());
        config.put("expectedAction", expectedActions.toString());

        // 单图链路这里你后续也可以改回真实 condition
        config.put("expectedCondition", mostProbableNextState.condition());

        imageSenderService.processImg(img, timestamp, stateMachineByName, config);
        return true;
    }

    private final Map<String, String> wfIdCache = new HashMap<>();

    private Map<String, String> buildConfig(String modelWithConfig) {
        String[] split = modelWithConfig.split("@");
        Map<String, String> config = new HashMap<>();
        if (split[0].equalsIgnoreCase("python")) {
            config.put("host", split[1]);
        } else {
            config.put("workspace_name", split[1]);
            config.put("workflow_name", split[2]);
            if (wfIdCache.containsKey(split[1] + split[2])) {
                config.put("workflow_id", wfIdCache.get(split[1] + split[2]));
            } else {
                String workflowId = roboflowWorkflowRepository
                        .findByWorkspaceNameAndWorkflowName(split[1], split[2])
                        .getWorkflowId();
                config.put("workflow_id", workflowId);
                wfIdCache.put(split[1] + split[2], workflowId);
            }
        }
        return config;
    }

    private ImageSender buildSenderService(String modelWithConfig) {
        return imageSenderService.getUseImageSender(modelWithConfig);
    }

    public Double getProgress(String user) {
        long processedFrames = imageSenderService.progressMap.getOrDefault(user, new HashMap<>()).size();
        long totalFrames = imageSenderService.totleFramesMap.getOrDefault(user, 1L);
        return (double) processedFrames / totalFrames;
    }

    public ResponseEntity<?> getFileResponse(String user) throws MalformedURLException {
        File videoFile = imageSenderService.tempFiles.get(user);
        if (!videoFile.exists()) {
            return ResponseEntity.notFound().build();
        }

        Resource videoResource = new UrlResource(videoFile.getAbsoluteFile().toURI());

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + videoFile.getName() + "\"")
                .body(videoResource);
    }
}
