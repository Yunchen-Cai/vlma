import { PresetNode } from "./PresetNode";

export class Preset {
    id: number;
    name: string;
    nodes: PresetNode[];

    constructor(id: number, name: string, nodes: PresetNode[] = []) {
        this.id = id;
        this.name = name;
        this.nodes = nodes;
    }

    toString(): string {
        return `Preset{id=${this.id}, name=${this.name}, nodes=[${this.nodes.map(n => n.toString()).join(", ")}]}`;
    }
}
