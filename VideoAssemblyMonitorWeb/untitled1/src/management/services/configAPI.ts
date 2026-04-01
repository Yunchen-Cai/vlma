// services/configAPI.ts

import axios from "axios";
import {host} from "../../Share.tsx";

/** ----------------------------------
 *  通用类型定义
 *-----------------------------------*/

/**
 * 与后端 /config/python 或 /config/roboflow 接口对接的请求体
 * 对应 ConfigController.hostAndPort
 */
export interface HostAndPort {
    host: string;
    port: string;
}

/**
 * 后端 QuotaConfig 实体类型，可根据实际情况扩展
 * （示例只包含一个 quota 字段）
 */
export interface QuotaConfig {
    quotas: SingleQuota[];
    quota_mode: "avgOffset" | "confidence" | "disabled";
    // 这里可根据实际需求扩展更多字段
    // e.g. { "quota": number, "reason": string }

}

export interface SingleQuota {
    type: string;
}

export interface SingleQuotaOfConf extends SingleQuota {
    proc: string;
    avg: string;
    std_dev: string;
    up_boundary: string;
    down_boundary: string;
}

export interface SingleQuotaOfOffset extends SingleQuota {
    proc: string;
    quota: string;
    up_boundary: string;
    up_ratio: string;
    down_boundary: string;
    down_ratio: string;
}

export interface StepStats {
    step_name: string;
    average_time: number;
    std_dev: number;
}

/**
 * 后端 /config/all 返回的配置整体。
 * 由于后端返回的是一个 JSON 字符串，也可自行确定结构。
 * 在这里示例一下常见字段（供前端反序列化）。
 */
export interface AllConfigs {
    pythonServerHost: string;
    pythonServerMainPort: string;
    roboflowHost: string;
    roboflowPort: string;
    useModel: Record<string, string>;
    modelQuotaConfig: Record<string, string>;
    // ... 其他字段
}

/** ----------------------------------
 *  与后端通信的方法
 *-----------------------------------*/

/**
 * test connection (GET /management/ping)
 * @returns true if success, false otherwise.
 */
export async function ping(): Promise<boolean> {
    let flag= true;
    await (axios.get<string>(host + "/management/ping", {
        responseType: "text",
    }).catch((err) => {
        console.log(err)
        flag = false
    }).then((res) => flag = flag && Object.prototype.hasOwnProperty.call(res, "data") && res?.data === "pa"));
    console.log(flag);
    return flag;
}

/**
 * test connection (GET /ping-rf)
 * @returns true if success, false otherwise.
 */
export async function pingRf(test_host: string, port: string): Promise<boolean> {
    let flag= true;
    await (axios.post<string>(host + "/ping-rf", {host: test_host, port: port}, {
        responseType: "text",
    }).catch((err) => {
        console.log(err)
        flag = false
    }).then((res) => flag = flag && Object.prototype.hasOwnProperty.call(res, "data") && res?.data === "pa"));
    console.log(flag);
    return flag;
}

/**
 * 获取全部配置 (GET /config/all)
 * @returns 后端返回的 JSON（已经作为对象解析）
 */
export async function getAllConfigs(): Promise<AllConfigs> {
    const response = await axios.get<string>(host + "/config/all", {
        responseType: "text",
    });
    return JSON.parse(response.data) as AllConfigs;
}

export async function fetchModels(): Promise<string[] | undefined> {
    try {
        const response = await fetch(host + "/config/model/all");
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return [];
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch legal models:", error);
    }
}

/**
 * 获取全部step-stats (GET /review/step-stats-all)
 * @returns 后端返回的 JSON（已经作为对象解析）
 */
export async function getStepStatsAll(): Promise<StepStats[]> {
    const response = await axios.get<string>(host + "/review/step-stats-all");
    console.log(response.data)
    return response.data as unknown as StepStats[];
}

/**
 * 获取 step-stats (GET /review/step-stats/{presetName} )
 * @param presetName 使用这个preset获取。
 * @returns 后端返回的 JSON（已经作为对象解析）
 */
export async function getStepStats(presetName: string): Promise<StepStats[]> {
    const response = await axios.get<string>(host + "/review/step-stats/" + presetName);
    console.log(response.data)
    return response.data as unknown as StepStats[];
}

/**
 * 一次性更新全部配置 (PUT /config/all)
 * @param newConfig AllConfigs 类型
 */
export async function updateAllConfigs(newConfig: AllConfigs): Promise<void> {
    // 后端实际上希望接收 string (JSON)，所以要 stringify
    await axios.put(host + "/config/all", JSON.stringify(newConfig), {
        headers: { "Content-Type": "application/json" },
    });
}

/**
 * 更新 Python 服务器配置 (PUT /config/python)
 */
export async function updatePythonConfig(hostAndPort: HostAndPort): Promise<void> {
    await axios.put(host + "/config/python", hostAndPort, {
        headers: { "Content-Type": "application/json" },
    });
}

/**
 * 更新 roboflow 服务器配置 (PUT /config/roboflow)
 */
export async function updateRoboflowConfig(hostAndPort: HostAndPort): Promise<void> {
    await axios.put(host + "/config/roboflow", hostAndPort, {
        headers: { "Content-Type": "application/json" },
    });
}

/**
 * 更新某个 preset 的模型类型 (PUT /config/model/preset/{presetName})
 * @param presetName Preset 名称
 * @param modelValue 模型值
 */
export async function updateUseModelPreset(presetName: string, modelValue: string): Promise<void> {
    // 注意：后端需要的是一个纯文本的 body
    await axios.put(host + `/config/model/preset/${presetName}`, modelValue, {
        headers: { "Content-Type": "application/json" },
    });
}

/**
 * 更新默认模型 (PUT /config/model/preset-default)
 */
export async function updateUseModelPresetDefault(modelValue: string): Promise<void> {
    await axios.put(host + "/config/model/preset-default", modelValue, {
        headers: { "Content-Type": "application/json" },
    });
}

/**
 * 更新某个 preset 的 QuotaConfig (PUT /config/quota/preset/{presetName})
 */
export async function updateQuotaConfig(presetName: string, quotaConfig: QuotaConfig): Promise<void> {
    await axios.put(host + `/config/quota/preset/${presetName}`, quotaConfig, {
        headers: { "Content-Type": "application/json" },
    });
}

/**
 * 更新默认模型的 QuotaConfig (PUT /config/quota/preset-default)
 */
export async function updateQuotaConfigDefault(quotaConfig: QuotaConfig): Promise<void> {
    await axios.put(host + "/config/quota/preset-default", quotaConfig, {
        headers: { "Content-Type": "application/json" },
    });
}
