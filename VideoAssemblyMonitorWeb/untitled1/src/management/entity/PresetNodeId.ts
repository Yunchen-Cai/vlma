
export class PresetNodeId {
    preset: number;
    number: number;

    constructor(preset: number, number: number) {
        this.preset = preset;
        this.number = number;
    }

    equals(other: PresetNodeId): boolean {
        return this.number === other.number && this.preset === other.preset;
    }

    toString(): string {
        return `PresetNodeId{preset=${this.preset}, number=${this.number}}`;
    }
}
