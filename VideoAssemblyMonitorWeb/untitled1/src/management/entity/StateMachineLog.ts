import { Preset } from "./Preset";

export class StateMachineLog {
    id: number;
    user: string;
    preset: Preset;
    start_time: Date;
    end_time: Date;
    duration: number;

    constructor(
        id: number,
        user: string,
        preset: Preset,
        start_time: Date,
        end_time: Date,
        duration: number,
    ) {
        this.id = id;
        this.user = user;
        this.preset = preset;
        this.start_time = start_time;
        this.end_time = end_time;
        this.duration = duration;
    }

}
