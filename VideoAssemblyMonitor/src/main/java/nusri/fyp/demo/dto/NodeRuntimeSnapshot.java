package nusri.fyp.demo.dto;

import java.util.List;

public record NodeRuntimeSnapshot(
        Integer number,
        String name,
        String condition,
        Integer rank,
        double realQuota,
        List<Integer> parentNumbers,
        List<String> actions
) {
}