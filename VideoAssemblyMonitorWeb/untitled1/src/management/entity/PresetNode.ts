import { PresetNodeId } from "./PresetNodeId";

export class PresetNode {
    name: string;
    id: PresetNodeId;
    real_quota: number;
    upper_quota: number;
    lower_quota: number;
    calculating_quota: number;
    parents: PresetNode[];
    actions: string[];
    rank: number;

    constructor(name: string, id: PresetNodeId, quota: number, upper_quota: number, lower_quota: number,calculating_quota: number , parents: PresetNode[], actions: string[] = [], rank: number = 0) {
        this.name = name;
        this.id = id;
        this.real_quota = quota;
        this.parents = parents;
        this.actions = actions;
        this.rank = rank;
        this.upper_quota = upper_quota;
        this.lower_quota = lower_quota;
        this.calculating_quota = calculating_quota;
    }


}
