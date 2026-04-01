package nusri.fyp.demo;

import lombok.extern.slf4j.Slf4j;
import org.opencv.core.Core;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.scheduling.annotation.EnableScheduling;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.stream.Stream;

/**
 * The main entry point for the Spring Boot application.
 * <br> This class initializes the Spring Boot application and enables various features such as scheduling, caching, and aspect-oriented programming.
 * @author Liu Binghong
 * @since 1.0
 */
@Slf4j
@SpringBootApplication
@EnableScheduling  // Enables scheduling support in Spring
@EnableAspectJAutoProxy  // Enables AspectJ auto proxying for aspect-oriented programming
@EnableCaching  // Enables caching support in Spring
public class DemoApplication {


    /**
     * The main method that serves as the entry point to the Spring Boot application.
     * <br> It triggers the Spring Boot application to start.
     *
     * @param args Command-line arguments passed to the application
     */
    public static void main(String[] args) {

        System.out.println("restart.enabled(sysprop)=" + System.getProperty("spring.devtools.restart.enabled"));

        try {
            Path srcPath = Paths.get("src");
            printDirectoriesAndJavaFiles(srcPath);
        } catch (IOException ignored) {
        }
        OpenCvLoader.load();

        SpringApplication.run(DemoApplication.class, args);
    }

    /**
     * Prints the directories and .java files under the given path.
     *
     * @param path The path to start looking from
     * @throws IOException If an I/O error occurs
     */
    private static void printDirectoriesAndJavaFiles(Path path) throws IOException {
        try (Stream<Path> paths = Files.walk(path)) {
            paths.filter(p -> p.toString().endsWith(".java") || Files.isDirectory(p))
                    .forEach(p -> System.out.println(p.toAbsolutePath()));
        }
    }
}
