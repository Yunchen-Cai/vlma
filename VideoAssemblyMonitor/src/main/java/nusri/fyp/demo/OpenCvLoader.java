package nusri.fyp.demo;

import java.util.concurrent.atomic.AtomicBoolean;

public final class OpenCvLoader {
    private static final AtomicBoolean LOADED = new AtomicBoolean(false);

    private OpenCvLoader() {}

    public static void load() {
        if (LOADED.compareAndSet(false, true)) {
            System.load("D:\\OpenCV460\\opencv\\build\\java\\x64\\opencv_java460.dll");
        }
    }
}
