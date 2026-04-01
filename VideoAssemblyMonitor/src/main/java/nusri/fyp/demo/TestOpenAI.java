package nusri.fyp.demo;

import okhttp3.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.Duration;

public class TestOpenAI {
    public static void main(String[] args) {
        try {
            String apiKey = System.getenv("OPENAI_API_KEY");
            if (apiKey == null || apiKey.isBlank()) {
                System.err.println("❌ 未读取到 OPENAI_API_KEY（请重启 IntelliJ，或在 Run/Debug 的 Environment variables 里手动添加）");
                System.exit(1);
            } else {
                System.out.println("✅ 读取到 OPENAI_API_KEY（已隐藏）: sk-********");
            }

            OkHttpClient client = new OkHttpClient.Builder()
                    .callTimeout(Duration.ofSeconds(60))
                    .connectTimeout(Duration.ofSeconds(30))
                    .readTimeout(Duration.ofSeconds(60))
                    .build();

            String json = """
            {
              "model": "gpt-4o-mini",
              "messages": [
                {"role": "system", "content": "你是一个简短回答的助手"},
                {"role": "user", "content": "写一句中文诗"}
              ]
            }
            """;

            Request request = new Request.Builder()
                    .url("https://api.openai.com/v1/chat/completions")
                    .addHeader("Authorization", "Bearer " + apiKey)
                    .addHeader("Content-Type", "application/json")
                    .post(RequestBody.create(json, MediaType.get("application/json")))
                    .build();

            try (Response response = client.newCall(request).execute()) {
                String body = response.body() != null ? response.body().string() : "";
                System.out.println("HTTP " + response.code());
                System.out.println("RAW BODY: " + body);

                if (!response.isSuccessful()) {
                    System.err.println("❌ API 调用失败（检查 key/网络/账单）：HTTP " + response.code());
                    System.exit(1);
                }

                ObjectMapper mapper = new ObjectMapper();
                JsonNode root = mapper.readTree(body);
                String content = root.at("/choices/0/message/content").asText();
                System.out.println("✅ 模型输出: " + content);
            }
        } catch (Exception e) {
            System.err.println("❌ 运行异常：");
            e.printStackTrace();
            System.exit(1);
        }
    }
}
