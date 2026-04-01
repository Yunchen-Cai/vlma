
export interface SinglePrediction {
    label: string;
    confidence: number;
    x: number;
    y: number;
    width: number;
    height: number;
    class_id: number;  // 或者使用更 JS/TS 习惯的字段名 "classId"
    clazz: string;     // 同理，如果希望改成 "clazz"
    detection_id: string;
    parent_id: string;
}

export type SinglePredictionsMap = Record<number, SinglePrediction[]>;

export interface RawSinglePrediction {
    label: string;
    confidence: number;
    x: number;
    y: number;
    width: number;
    height: number;
    class_id: number;
    class: string; // 注意，这里和后端返回的一致
    detection_id: string;
    parent_id: string;
}

// 2. 定义一个原始的 Prediction Map 类型：时间戳 -> 原始预测数组
export type RawSinglePredictionsMap = Record<number, RawSinglePrediction[]>;