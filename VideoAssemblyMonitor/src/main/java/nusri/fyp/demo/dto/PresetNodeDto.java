package nusri.fyp.demo.dto;

import lombok.Getter;
import lombok.Setter;
import nusri.fyp.demo.entity.Preset;
import nusri.fyp.demo.entity.PresetNode;
import nusri.fyp.demo.entity.PresetNodeId;
import nusri.fyp.demo.entity.QuotaConfig;

import java.util.*;
import java.util.stream.Collectors;

/**
 * DTO corresponding to the {@link nusri.fyp.demo.entity.PresetNode}.
 * <br>
 * Contains node name, composite primary key {@link PresetNodeIdDto}, quota, rank, and parent nodes along with triggerable actions.
 */
@Getter
@Setter
public class PresetNodeDto {
    /**
     * The name of the node, e.g., "OpenDoorStep".
     */
    private String name;

    /**
     * The DTO corresponding to the composite primary key.
     */
    private PresetNodeIdDto id;  // Composite primary key

    /**
     * The actual quota value.
     */
    private double realQuota;

    private double upperQuota;
    private double lowerQuota;
    private double calculatingQuota;

    /**
     * The rank or order of the node (optional).
     */
    private int rank;

    /**
     * A set of parent nodes in DTO form.
     */
    private Set<PresetNodeDto> parents;  // Set of parent nodes

    /**
     * A list of actions that can be triggered by the node.
     */
    private List<String> actions;

    /**
     * Constructs a DTO from the {@link nusri.fyp.demo.entity.PresetNode} entity.
     *
     * @param presetNode The preset node entity.
     * @param quotaConfig The quota config.
     */
    public PresetNodeDto(PresetNode presetNode, QuotaConfig quotaConfig) {
        this.name = presetNode.getName();
        this.id = new PresetNodeIdDto(presetNode.getId());
        this.realQuota = presetNode.getRealQuota();
        this.rank = presetNode.getRank();
        this.parents = presetNode.getParents().stream().map(o-> new PresetNodeDto(o, quotaConfig)).collect(Collectors.toSet());
        this.actions = presetNode.getActions();
        this.upperQuota = presetNode.toNode().getUpperQuota(quotaConfig);
        this.lowerQuota = presetNode.toNode().getLowerQuota(quotaConfig);
        this.calculatingQuota = presetNode.toNode().getCalculateQuota(quotaConfig);
    }

    public PresetNodeDto(NodeRuntimeSnapshot presetNode, QuotaConfig quotaConfig, Preset preset) {
        this.name = presetNode.name();
        this.id = new PresetNodeIdDto(new PresetNodeId(preset, presetNode.number()));
        this.realQuota = presetNode.realQuota();
        this.rank = presetNode.rank();

        this.actions = presetNode.actions() == null
                ? new ArrayList<>()
                : new ArrayList<>(presetNode.actions());

        this.parents = presetNode.parentNumbers() == null
                ? new HashSet<>()
                : presetNode.parentNumbers().stream()
                .map(parentNumber -> {
                    try {
                        PresetNode parentNode = preset.getNode(parentNumber);
                        return parentNode == null ? null : new PresetNodeDto(parentNode, quotaConfig);
                    } catch (Throwable e) {
                        return null;
                    }
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());

        try {
            PresetNode currentNode = preset.getNode(presetNode.number());
            if (currentNode != null) {
                this.upperQuota = currentNode.toNode().getUpperQuota(quotaConfig);
                this.lowerQuota = currentNode.toNode().getLowerQuota(quotaConfig);
                this.calculatingQuota = currentNode.toNode().getCalculateQuota(quotaConfig);
            }
        } catch (Throwable e) {
            this.upperQuota = 0;
            this.lowerQuota = 0;
            this.calculatingQuota = 0;
        }
    }

    /**
     * Prints debug information showing the main fields.
     *
     * @return The string representation.
     */
    @Override
    public String toString() {
        return "PresetNodeDto{" +
                "name='" + name + '\'' +
                ", id=" + id +
                '}';
    }
}