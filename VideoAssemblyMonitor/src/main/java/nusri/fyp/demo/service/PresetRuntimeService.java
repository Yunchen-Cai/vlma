package nusri.fyp.demo.service;

import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import nusri.fyp.demo.dto.NodeRuntimeSnapshot;
import nusri.fyp.demo.dto.PresetRuntimeSnapshot;
import nusri.fyp.demo.entity.Preset;
import nusri.fyp.demo.entity.PresetNode;
import nusri.fyp.demo.repository.PresetRepository;
import org.hibernate.Hibernate;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class PresetRuntimeService {

    private final PresetRepository presetRepository;

    @Transactional
    public PresetRuntimeSnapshot loadSnapshot(String presetName) {
        Preset preset = presetRepository.findPresetByName(presetName).stream().findAny()
                .orElseThrow(() -> new IllegalArgumentException("Preset not found: " + presetName));

        Hibernate.initialize(preset.getNodes());

        List<NodeRuntimeSnapshot> nodes = preset.getNodes().stream()
                .map(this::toSnapshot)
                .toList();

        return new PresetRuntimeSnapshot(preset.getName(), nodes);
    }

    private NodeRuntimeSnapshot toSnapshot(PresetNode node) {
        Hibernate.initialize(node.getParents());
        Hibernate.initialize(node.getActions());

        List<Integer> parentNumbers = node.getParents() == null
                ? List.of()
                : node.getParents().stream()
                    .map(o -> o.getId().getNumber())
                    .toList();

        List<String> actions = node.getActions() == null
                ? List.of()
                : List.copyOf(node.getActions());

        return new NodeRuntimeSnapshot(
                node.getId().getNumber(),
                node.getName(),
                node.getCondition(),
                node.getRank(),
                node.getRealQuota(),
                parentNumbers,
                actions
        );
    }
}