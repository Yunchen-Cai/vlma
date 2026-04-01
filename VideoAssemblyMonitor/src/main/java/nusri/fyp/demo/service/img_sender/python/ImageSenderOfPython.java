package nusri.fyp.demo.service.img_sender.python;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.extern.slf4j.Slf4j;
import nusri.fyp.demo.repository.PythonServerRepository;
import nusri.fyp.demo.service.img_sender.ImageSender;
import nusri.fyp.demo.service.img_sender.ImageSenderService;
import nusri.fyp.demo.state_machine.AbstractActionObservation;
import nusri.fyp.demo.state_machine.ActionObservation;
import nusri.fyp.demo.state_machine.ActionObservationWithCndctnAchv;
import org.opencv.core.Mat;
import org.opencv.core.MatOfByte;
import org.opencv.imgcodecs.Imgcodecs;
import org.springframework.http.*;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.opencv.core.Rect;
import org.opencv.core.Size;
import org.opencv.imgproc.Imgproc;


import java.io.File;
import java.util.*;
import java.util.concurrent.CancellationException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;

/**
 * Single-backend version (no load balancing), adapted for new Python backend.
 */
@Slf4j
public class ImageSenderOfPython implements ImageSender {

    public static final boolean USE_PYTHON = false;

    private final ObjectMapper objectMapper;
    private final ImageSenderService imageSenderService;

    public ImageSenderOfPython(ImageSenderService imageSenderService,
                               ObjectMapper objectMapper,
                               PythonServerRepository pythonServerRepository) {
        this.imageSenderService = imageSenderService;
        this.objectMapper = objectMapper;
        // pythonServerRepository kept for compatibility with current Spring wiring.
    }

    @Override
    public List<AbstractActionObservation> sendFrame(Mat frame, Map<String, String> config) {
        String baseUrl = resolveBaseUrl(config);
        byte[] frameBytes = matToByteArray(frame, config);
        return sendByteArray(frameBytes, baseUrl, config);
    }

    @Override
    public List<AbstractActionObservation> sendFrame(String frame, Map<String, String> config) {
        String baseUrl = resolveBaseUrl(config);

        byte[] decodedBytes = decodeBase64Image(frame);
        if (decodedBytes == null || decodedBytes.length == 0) {
            log.warn("Empty/invalid base64 image payload");
            return new ArrayList<>();
        }

        return sendByteArray(decodedBytes, baseUrl, config);
    }

    private byte[] decodeBase64Image(String input) {
        if (input == null) return new byte[0];

        String s = input.trim();

        // Handle data URL: data:image/png;base64,xxxxx
        int comma = s.indexOf(',');
        if (s.startsWith("data:") && comma >= 0) {
            s = s.substring(comma + 1);
        }

        // Remove whitespace/newlines
        s = s.replaceAll("\\s+", "");

        // Try standard base64 first
        try {
            return Base64.getDecoder().decode(s);
        } catch (IllegalArgumentException ignored) {
        }

        // Fallback: URL-safe base64 (- and _)
        try {
            return Base64.getUrlDecoder().decode(s);
        } catch (IllegalArgumentException e) {
            log.warn("Invalid base64 payload (first 40 chars): {}", s.substring(0, Math.min(40, s.length())));
            return new byte[0];
        }
    }


    @Override
    public CompletableFuture<List<AbstractActionObservation>> sendFrameAsync(Mat frame, String user, Map<String, String> config) {
        String baseUrl = resolveBaseUrl(config);

        CompletableFuture<List<AbstractActionObservation>> futureResult = CompletableFuture.supplyAsync(() -> {
            try {
                byte[] frameBytes = matToByteArray(frame, config);
                return sendByteArray(frameBytes, baseUrl, config)
                        .stream()
                        .map(o -> (AbstractActionObservation) o)
                        .toList();
            } catch (CompletionException | CancellationException e) {
                log.info("Task was cancelled by user");
                return new ArrayList<>();
            }
        });

        List<CompletableFuture<List<AbstractActionObservation>>> userFutures =
                imageSenderService.sendingProcesses.getOrDefault(user, new ArrayList<>());
        userFutures.add(futureResult);
        imageSenderService.sendingProcesses.put(user, userFutures);

        return futureResult;
    }

    public void interruptSendingProcesses(String user) {
        if (!imageSenderService.sendingProcesses.containsKey(user)) {
            return;
        }
        List<CompletableFuture<List<AbstractActionObservation>>> futures = imageSenderService.sendingProcesses.get(user);
        try {
            futures.forEach(future -> future.cancel(true));
        } catch (Exception ignored) {
        }
    }

    @Override
    public void interrupt(String user) {
        interruptSendingProcesses(user);
        imageSenderService.totleFramesMap.remove(user);
        imageSenderService.progressMap.remove(user);
        imageSenderService.sendingProcesses.remove(user);

        if (imageSenderService.tempFiles.containsKey(user)) {
            File file = imageSenderService.tempFiles.get(user);
            new Thread(() -> {
                int cnt = 0;
                while (!file.delete()) {
                    cnt++;
                    if (cnt == 5) break;
                }
                imageSenderService.tempFiles.remove(user);
            }).start();
        }
    }

    private String resolveBaseUrl(Map<String, String> config) {
        // Your python PORT=5005, so default port is 5005
        String host = config.getOrDefault("host", "http://localhost");
        String port = config.getOrDefault("port", "5005");

        if (host.endsWith("/")) host = host.substring(0, host.length() - 1);

        // If host already contains port (e.g., http://127.0.0.1:5005), don't append port again
        if (host.matches(".*:\\d+$")) {
            return host;
        }
        return host + ":" + port;
    }

    private byte[] matToByteArray(Mat mat, Map<String, String> config) {
        int reshapeTo = resolveReshapeTo(config); // default 720
        Mat processed = preprocessMat16by9AndResize(mat, reshapeTo);

        MatOfByte buf = new MatOfByte();
        if (!Imgcodecs.imencode(".png", processed, buf)) {
            log.warn("Error occurred when converting Mat to byte array");
        }

        // 注意：processed 注意释放（如果是 submat/resize 产生的临时 Mat）
        // 为避免误释放原 mat，这里只释放我们 clone/resize 出来的 Mat
        // preprocessMat16by9AndResize 会返回 clone/resize 出来的 Mat，安全 release
        processed.release();

        return buf.toArray();
    }

    private int resolveReshapeTo(Map<String, String> config) {
        String v = config.getOrDefault("reshapeTo", "720");
        try {
            int h = Integer.parseInt(v.trim());
            // 防御：太小没意义，给个下限
            return Math.max(h, 1);
        } catch (Exception ignored) {
            return 720;
        }
    }

    /**
     * 1) center-crop to 16:9
     * 2) if cropped >= target (W=H*16/9, H=reshapeTo), resize down to target
     * 3) if cropped smaller than target, keep as-is (no upscaling)
     *
     * Always returns a NEW Mat (clone/resized) so caller can safely release().
     */
    private Mat preprocessMat16by9AndResize(Mat src, int targetH) {
        int srcW = src.cols();
        int srcH = src.rows();

        // 如果输入异常，直接 clone
        if (srcW <= 0 || srcH <= 0) {
            return src.clone();
        }

        // -------- 1) Center crop to 16:9 --------
        // Desired aspect = 16/9
        double desired = 16.0 / 9.0;
        double current = (double) srcW / (double) srcH;

        int cropW, cropH;
        if (current > desired) {
            // too wide -> crop width
            cropH = srcH;
            cropW = (int) Math.round(srcH * desired);
        } else {
            // too tall -> crop height
            cropW = srcW;
            cropH = (int) Math.round(srcW / desired);
        }

        cropW = Math.min(cropW, srcW);
        cropH = Math.min(cropH, srcH);

        int x = (srcW - cropW) / 2;
        int y = (srcH - cropH) / 2;

        Rect roi = new Rect(x, y, cropW, cropH);
        Mat cropped = new Mat(src, roi).clone(); // clone to detach from src

        // -------- 2) Downscale to target if big enough --------
        int targetW = (int) Math.round(targetH * desired); // 16:9 width
        if (cropped.rows() >= targetH && cropped.cols() >= targetW) {
            Mat resized = new Mat();
            Imgproc.resize(cropped, resized, new Size(targetW, targetH), 0, 0, Imgproc.INTER_AREA);
            cropped.release();
            return resized;
        }

        // -------- 3) Smaller than target -> keep as-is --------
        return cropped;
    }


    /**
     * Sends raw PNG bytes to python backend and converts response to a single ActionObservation.
     */
    public List<AbstractActionObservation> sendByteArray(byte[] frameBytes, String baseUrl, Map<String, String> config) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_OCTET_STREAM);
        headers.setAccept(List.of(MediaType.APPLICATION_JSON));

        // Optional expectations passed to python backend
        String expectTool = firstNonBlank(config.get("expectTool"), config.get("expectedTool"), config.get("X-Expect-Tool"));
        String expectAction = firstNonBlank(config.get("expectAction"), config.get("expectedAction"), config.get("X-Expect-Action"));
        String expectCondition = firstNonBlank(config.get("expectCondition"), config.get("expectedCondition"), config.get("X-Expect-Condition"));
        if (expectTool != null) headers.set("X-Expect-Tool", expectTool);
        if (expectAction != null) headers.set("X-Expect-Action", expectAction);
        if (expectCondition != null) headers.set("X-Expect-Condition", expectCondition);

        HttpEntity<byte[]> requestEntity = new HttpEntity<>(frameBytes, headers);

        try {
            String url = normalizeHttpUrl(baseUrl) + "/process_image";
            log.debug("Sending image to {}", url);

            RestTemplate restTemplate = new RestTemplate();
            ResponseEntity<String> response = restTemplate.exchange(
                    url,
                    HttpMethod.POST,
                    requestEntity,
                    String.class
            );

            int status = response.getStatusCode().value();
            String body = response.getBody();

            if (status == 503) {
                log.info("Python backend busy (503). Returning empty result.");
                return new ArrayList<>();
            }

            if (body == null || body.isBlank()) {
                return new ArrayList<>();
            }

            PythonProcessResult result = objectMapper.readValue(body, PythonProcessResult.class);

            // todo 记得改回debug
            log.info(result.toString());

            // busy with 200
            if ("busy".equalsIgnoreCase(result.getStatus())) {
                return new ArrayList<>();
            }

            // explicit error
            if (result.getError() != null && !result.getError().isBlank()) {
                log.warn("Python backend returned error: {}", result.getError());
                return new ArrayList<>();
            }

            AbstractActionObservation ao = toActionObservation(result, expectCondition);
            log.debug(ao.s());
            return List.of(ao);

        } catch (RestClientException e) {
            log.warn("HTTP error processing image: {}", e.getMessage());
        } catch (JsonProcessingException e) {
            log.warn("Error parsing JSON response: {}", e.getMessage());
        } catch (Exception e) {
            log.warn("Unexpected error when sending frame: {}", e.getMessage());
        }

        return new ArrayList<>();
    }

    private String normalizeHttpUrl(String baseUrl) {
        if (baseUrl == null) return "http://localhost:5005";
        String s = baseUrl.trim();
        while (s.endsWith("/")) s = s.substring(0, s.length() - 1);
        if (!s.startsWith("http://") && !s.startsWith("https://")) {
            s = "http://" + s;
        }
        return s;
    }


    private AbstractActionObservation toActionObservation(PythonProcessResult r, String expectedCondition) {
        String action = normalizeOrUnknown(r.getAction());
        String tool = normalizeOrUnknown(r.getTool());
        String part = normalizeOrUnknown(r.getPart());

        // Format: [action] By [tool] [part]  (spaces around "By")
        String actionAndObject = action + "_By_" + tool + "_" + part;

        if (r.verification) {
            ActionObservationWithCndctnAchv ao = new ActionObservationWithCndctnAchv();
            ao.setActionAndObject(actionAndObject);
            double prob = parseConfidenceOrDefault(r.getConfidence(), 1.0);
            ao.setProbability(prob);
            ao.setAchievedCondition(expectedCondition);
            return ao;
        } else {
            ActionObservation ao = new ActionObservation();
            ao.setActionAndObject(actionAndObject);
            double prob = parseConfidenceOrDefault(r.getConfidence(), 1.0);
            ao.setProbability(prob);
            return ao;
        }
    }

    private double parseConfidenceOrDefault(Object confidence, double defaultValue) {
        if (confidence == null) return defaultValue;

        // Case 1: numeric types
        if (confidence instanceof Number n) {
            return n.doubleValue();
        }

        // Case 2: string like "0.83"
        String s = confidence.toString().trim();
        if (s.isEmpty()) return defaultValue;

        try {
            return Double.parseDouble(s);
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    private String normalizeOrUnknown(String s) {
        if (s == null) return "Unknown";
        String t = s.trim();
        return t.isEmpty() ? "Unknown" : t;
    }

    private static String firstNonBlank(String... vals) {
        if (vals == null) return null;
        for (String v : vals) {
            if (v != null && !v.isBlank()) return v;
        }
        return null;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @JsonIgnoreProperties(ignoreUnknown = true)
    static class PythonProcessResult {

        // busy/error
        private String status;
        private String error;

        // normal fields
        private Boolean verification;
        private String tool;
        private String action;
        private String part;
        private String reason;

        // NEW: python returns confidence (could be number or string)
        @JsonProperty("confidence")
        private Object confidence;

        @JsonProperty("_meta")
        private Meta meta;

        @Getter
        @Setter
        @NoArgsConstructor
        @JsonIgnoreProperties(ignoreUnknown = true)
        static class Meta {
            private String fps;

            @JsonProperty("req_id")
            private Long reqId;
        }

        @Override
        public String toString() {
            return "PythonProcessResult{" +
                    "status='" + status + '\'' +
                    ", error='" + error + '\'' +
                    ", verification=" + verification +
                    ", tool='" + tool + '\'' +
                    ", action='" + action + '\'' +
                    ", part='" + part + '\'' +
                    ", reason='" + reason + '\'' +
                    ", confidence=" + confidence +
                    '}';
        }
    }

}
