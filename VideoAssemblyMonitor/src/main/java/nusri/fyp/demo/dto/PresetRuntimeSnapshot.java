package nusri.fyp.demo.dto;

import java.util.List;

public record PresetRuntimeSnapshot(
        String presetName,
        List<NodeRuntimeSnapshot> nodes
) {
}