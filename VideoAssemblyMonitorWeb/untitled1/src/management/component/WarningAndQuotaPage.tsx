import React, {useEffect, useState} from "react";
import {Button, InputNumber, message, Modal, Radio, Select, Table, Tooltip, Typography} from "antd";
import {InfoCircleOutlined} from "@ant-design/icons";
import {useLanguage} from "../../LanguageContext";
import { probit } from "simple-statistics";

import {
    getStepStats,
    getStepStatsAll,
    QuotaConfig,
    SingleQuotaOfConf,
    SingleQuotaOfOffset,
    StepStats,
    updateQuotaConfig,
    updateQuotaConfigDefault
} from "../services/configAPI.ts";
import {host} from "../../Share.tsx";

const { Title } = Typography;

interface QuotaRow {
    step_name: string;
    quota: number;
    up_percent: number;
    down_percent: number;
}

interface ConfidenceRow {
    step_name: string;
    average_time: number;
    std_dev: number;
    upper: number; // 接受上界
    lower: number; // 接受下界
}

export const WarningAndQuotaPage: React.FC = () => {
    const { language } = useLanguage();

    // 用于选择Preset
    const [selectedPreset, setSelectedPreset] = useState<string>("ALL");
    // 是否已计算平均时间
    const [statsCalculated, setStatsCalculated] = useState<boolean>(false);
    // 平均时间与标准差数据
    const [statsData, setStatsData] = useState<StepStats[]>([]);
    // 平均时间指定偏移模式下的表格
    const [quotaData, setQuotaData] = useState<QuotaRow[]>([]);
    // 置信度检验模式下的表格
    const [confidenceData, setConfidenceData] = useState<ConfidenceRow[]>([]);
    // 当前选择的Quota模式
    const [quotaMode, setQuotaMode] = useState<string>("avgOffset");
    // 弹窗：展示平均时间/标准差
    const [statsModalVisible, setStatsModalVisible] = useState<boolean>(false);
    // 在平均时间指定偏移模式下的全局上移/下移百分比
    const [globalUpPercent, setGlobalUpPercent] = useState<number>(0);
    const [globalDownPercent, setGlobalDownPercent] = useState<number>(0);
    // 置信度
    const [confidence, setConfidence] = useState<number>(95);

    // 用于存储从后端获取到的 preset 列表
    const [presets, setPresets] = useState<string[]>([]);

    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

    useEffect(() => {
        const fetchPresets = async () => {
            try {
                const response = await fetch(host + "/all-preset");
                if (!response.ok) {
                    console.error(`HTTP error! status: ${response.status}`);
                }
                const data: string[] = await response.json();
                setPresets(data);
            } catch (error) {
                console.error("Failed to fetch presets:", error);
            }
        };
        fetchPresets();
        const intervalId = setInterval(fetchPresets, 1000);
        return () => {
            clearInterval(intervalId);
        };
    }, []);

    // 计算平均时间和标准差（按钮 2）
    const handleCalculateStats = () => {
        if (selectedPreset === "ALL") {
            getStepStatsAll().then(o => {
                updateMockStats(o);
            });
        } else {
            getStepStats(selectedPreset).then(o => {
                updateMockStats(o);
            });
        }
    };

    const updateMockStats = (mockStats: StepStats[]) => {
        setStatsData(mockStats);
        setStatsModalVisible(true);
        setStatsCalculated(true);

        // 更新 quotaData（如果之前没有导入过，则初始化）
        const newQuotaData: QuotaRow[] = mockStats.map((s) => ({
            step_name: s.step_name,
            quota: s.average_time,
            up_percent: 10,
            down_percent: 10,
        }));
        setQuotaData(newQuotaData);

        // 更新 confidenceData
        const factor = getZScoreFromConfidence(confidence);
        const newConfidenceData: ConfidenceRow[] = mockStats.map((s) => ({
            step_name: s.step_name,
            average_time: s.average_time,
            std_dev: s.std_dev,
            upper: s.average_time + factor * s.std_dev,
            lower: s.average_time - factor * s.std_dev,
        }));
        setConfidenceData(newConfidenceData);
    };

    /**
     * 传入置信度（百分数），例如 95 表示 95%。返回该置信度对应的 z-score。
     */
    function getZScoreFromConfidence(confidencePercent: number): number {
        const c = confidencePercent / 100;
        // double-sided => 0.975 for 95%
        const p = (1 + c) / 2;
        return probit(p); // simple-statistics 提供的 probit，可得到对应 z 分位
    }

    // 导入平均时间
    const handleImportAvgTime = () => {
        if (!statsCalculated) {
            message.warning(language.warningAndQuota.importAvgTimeDisabledTip);
            return;
        }
        const newQuotaData = quotaData.map((row) => {
            const matchedStat = statsData.find((s) => s.step_name === row.step_name);
            if (matchedStat) {
                return { ...row, quota: matchedStat.average_time };
            }
            return row;
        });
        setQuotaData(newQuotaData);
        message.success("Imported average time successfully!");
    };

    // 统一设置上移百分比
    const handleSetAllUpPercent = () => {
        const updated = quotaData.map((row) => ({
            ...row,
            up_percent: globalUpPercent,
        }));
        setQuotaData(updated);
        message.success("Up shift percent updated for all steps");
    };

    // 统一设置下移百分比
    const handleSetAllDownPercent = () => {
        const updated = quotaData.map((row) => ({
            ...row,
            down_percent: globalDownPercent,
        }));
        setQuotaData(updated);
        message.success("Down shift percent updated for all steps");
    };

    // 在置信度模式下点击提交
    const handleSetConfidence = () => {
        const factor = getZScoreFromConfidence(confidence);
        const newConfidenceData = statsData.map((s) => ({
            step_name: s.step_name,
            average_time: s.average_time,
            std_dev: s.std_dev,
            upper: s.average_time + factor * s.std_dev,
            lower: (s.average_time - factor * s.std_dev) < 0 ? 0 : (s.average_time - factor * s.std_dev),
        }));
        setConfidenceData(newConfidenceData);
    };

    // =========== 关键：使用 Modal.confirm 的正确写法 ===========
    const handleSubmit = () => {
        // 这里使用 Modal.confirm 显示确认弹窗
        setIsSubmitting(true);
    };

    const handleModalOk = async () => {
        try {
            let qc: QuotaConfig;
            if (quotaMode === "disabled") {
                qc = { quota_mode: quotaMode, quotas: [] };
            } else if (quotaMode === "avgOffset") {
                const quotas: SingleQuotaOfOffset[] = [];
                for (const row of quotaData) {
                    quotas.push({
                        proc: row.step_name,
                        quota: row.quota.toString(),
                        down_ratio: row.down_percent.toString(),
                        up_ratio: row.up_percent.toString(),
                        down_boundary: (row.quota * (1 - row.down_percent / 100)).toFixed(2),
                        up_boundary: (row.quota * (1 + row.up_percent / 100)).toFixed(2),
                        type: "offset",
                    });
                }
                qc = {
                    quota_mode: "avgOffset",
                    quotas: quotas,
                };
            } else {
                const quotas: SingleQuotaOfConf[] = [];
                for (const row of confidenceData) {
                    quotas.push({
                        avg: row.average_time.toString(),
                        std_dev: row.std_dev.toString(),
                        proc: row.step_name,
                        up_boundary: row.upper.toFixed(2),
                        down_boundary: row.lower.toFixed(2),
                        type: "conf",
                    });
                }
                qc = {
                    quota_mode: "confidence",
                    quotas: quotas,
                };
            }

            if (selectedPreset === "ALL") {
                await updateQuotaConfigDefault(qc);
            } else {
                await updateQuotaConfig(selectedPreset, qc);
            }
            message.success("Submitted changes!");
        } catch (err) {
            message.error("Failed to submit changes: " + String(err));
        }
        setIsSubmitting(false); // 关闭 Modal
    };

    const handleModalCancel = () => {
        setIsSubmitting(false); // 关闭 Modal
    };

    // quotaData表格列
    const quotaColumns = [
        {
            title: language.warningAndQuota.stepColumn,
            dataIndex: "step_name",
            key: "step_name",
        },
        {
            title: language.warningAndQuota.quotaTime,
            dataIndex: "quota",
            key: "quota",
            render: (_: number, record: QuotaRow) => (
                <InputNumber
                    min={0}
                    value={record.quota}
                    onChange={(val) => {
                        if (val !== null) {
                            updateQuotaRow(record.step_name, "quota", val);
                        }
                    }}
                />
            ),
        },
        {
            title: (
                <>
                    {language.warningAndQuota.upPercentLabel}{" "}
                    <Tooltip title={language.warningAndQuota.upPercentInfo}>
                        <InfoCircleOutlined />
                    </Tooltip>
                </>
            ),
            dataIndex: "upPercent",
            key: "upPercent",
            render: (_: number, record: QuotaRow) => (
                <InputNumber
                    min={0}
                    value={record.up_percent}
                    onChange={(val) => {
                        if (val !== null) {
                            updateQuotaRow(record.step_name, "up_percent", val);
                        }
                    }}
                />
            ),
        },
        {
            title: language.warningAndQuota.upBoundaryTime,
            key: "upBoundary",
            render: (_: number, record: QuotaRow) => {
                const upBoundary = record.quota * (1 + record.up_percent / 100);
                return upBoundary.toFixed(2);
            },
        },
        {
            title: (
                <>
                    {language.warningAndQuota.downPercentLabel}{" "}
                    <Tooltip title={language.warningAndQuota.downPercentInfo}>
                        <InfoCircleOutlined />
                    </Tooltip>
                </>
            ),
            dataIndex: "downPercent",
            key: "downPercent",
            render: (_: number, record: QuotaRow) => (
                <InputNumber
                    min={0}
                    value={record.down_percent}
                    onChange={(val) => {
                        if (val !== null) {
                            updateQuotaRow(record.step_name, "down_percent", val);
                        }
                    }}
                />
            ),
        },
        {
            title: language.warningAndQuota.downBoundaryTime,
            key: "downBoundary",
            render: (_: number, record: QuotaRow) => {
                const downBoundary = record.quota * (1 - record.down_percent / 100);
                return downBoundary.toFixed(2);
            },
        },
    ];

    const updateQuotaRow = (
        stepName: string,
        field: keyof QuotaRow,
        value: number
    ) => {
        const updated = quotaData.map((row) => {
            if (row.step_name === stepName) {
                return { ...row, [field]: value };
            }
            return row;
        });
        setQuotaData(updated);
    };

    // confidence表格列
    const confidenceColumns = [
        {
            title: language.warningAndQuota.stepColumn,
            dataIndex: "step_name",
            key: "step_name",
        },
        {
            title: language.warningAndQuota.averageTimeColumn,
            dataIndex: "average_time",
            key: "average_time",
        },
        {
            title: language.warningAndQuota.stdDevColumn,
            dataIndex: "std_dev",
            key: "stdDev",
        },
        {
            title: language.warningAndQuota.acceptanceUpper,
            dataIndex: "upper",
            key: "upper",
            render: (val: number) => val.toFixed(2),
        },
        {
            title: language.warningAndQuota.acceptanceLower,
            dataIndex: "lower",
            key: "lower",
            render: (val: number) => val.toFixed(2),
        },
    ];

    return (
        <div
            style={{
                marginTop: 36,
                padding: "24px 60px",
                display: "flex",
                flexDirection: "column",
                gap: "24px",
            }}
        >
            <Title>{language.warningAndQuota.pageTitle}</Title>
            {/* 1. 选择Preset */}
            <div
                style={{
                    padding: 0,
                    display: "flex",
                    flexDirection: "row",
                    gap: "24px",
                    justifyContent: "left",
                    alignItems: "center",
                    width: "100%",
                }}
            >
                <label style={{ marginRight: 12, padding: "12px 0" }}>
                    {language.warningAndQuota.presetSelectLabel}:
                </label>
                <Select
                    style={{ width: 300 }}
                    value={selectedPreset}
                    onChange={(val) => setSelectedPreset(val)}
                    options={[
                        { value: "ALL", label: language.warningAndQuota.presetSelectAll },
                        ...presets.map((p) => ({ value: p, label: p })),
                    ]}
                />
            </div>

            {/* 2. 按钮：计算平均时间/标准差 */}
            <div style={{ height: "auto" }}>
                <Button type="primary" onClick={handleCalculateStats}>
                    {language.warningAndQuota.calculateStatsButton}
                </Button>
            </div>

            {/* 模态框查看 计算结果（这是受控 Modal，不是 confirm） */}
            <Modal
                title={language.warningAndQuota.calculateStatsModalTitle}
                open={statsModalVisible}
                onOk={() => setStatsModalVisible(false)}
                onCancel={() => setStatsModalVisible(false)}
                footer={[
                    <Button
                        key="cancel"
                        onClick={() => setStatsModalVisible(false)}
                        type="primary"
                    >
                        {language.common.confirmOk}
                    </Button>,
                ]}
            >
                <Table
                    columns={[
                        {
                            title: language.warningAndQuota.stepColumn,
                            dataIndex: "stepName",
                        },
                        {
                            title: language.warningAndQuota.averageTimeColumn,
                            dataIndex: "averageTime",
                        },
                        {
                            title: language.warningAndQuota.stdDevColumn,
                            dataIndex: "stdDev",
                        },
                    ]}
                    dataSource={statsData.map((s, idx) => ({
                        key: idx,
                        stepName: s.step_name,
                        averageTime: s.average_time,
                        stdDev: s.std_dev,
                    }))}
                    pagination={false}
                    size="small"
                />
            </Modal>

            {/* 3. 选择Quota模式 */}
            <div style={{ marginBottom: 24 }}>
                <label style={{ marginRight: 12 }}>
                    {language.warningAndQuota.quotaModeSelectLabel}:
                </label>
                <Radio.Group
                    optionType="button"
                    buttonStyle="solid"
                    value={quotaMode}
                    onChange={(e) => setQuotaMode(e.target.value)}
                >
                    <Radio value="avgOffset">
                        {language.warningAndQuota.quotaModeAvgOffset}
                    </Radio>
                    <Radio value="confidence">
                        {language.warningAndQuota.quotaModeConfidence}
                    </Radio>
                    <Radio value="disabled">
                        {language.warningAndQuota.quotaModeDisabled}
                    </Radio>
                </Radio.Group>
            </div>

            {quotaMode === "avgOffset" && (
                <>
                    {/* 导入平均时间按钮 */}
                    <div style={{ marginBottom: 24 }}>
                        <Button
                            onClick={handleImportAvgTime}
                            disabled={!statsCalculated}
                            title={
                                !statsCalculated
                                    ? language.warningAndQuota.importAvgTimeDisabledTip
                                    : ""
                            }
                        >
                            {language.warningAndQuota.importAvgTimeButton}
                        </Button>
                    </div>

                    {/* 统一设置上移百分比、下移百分比 */}
                    <div style={{ marginBottom: 24 }}>
                        <div style={{ marginBottom: 24 }}>
                            <label style={{ marginRight: 12 }}>
                                {language.warningAndQuota.upPercentLabel}{" "}
                                <Tooltip title={language.warningAndQuota.upPercentInfo}>
                                    <InfoCircleOutlined />
                                </Tooltip>
                                :
                            </label>
                            <InputNumber
                                min={0}
                                value={globalUpPercent}
                                onChange={(val) => setGlobalUpPercent(val || 0)}
                                style={{ marginRight: 24 }}
                            />
                            <Button onClick={handleSetAllUpPercent}>
                                {language.warningAndQuota.setAllUpPercentButton}
                            </Button>
                        </div>

                        <div style={{ marginBottom: 24 }}>
                            <label style={{ marginRight: 12 }}>
                                {language.warningAndQuota.downPercentLabel}{" "}
                                <Tooltip title={language.warningAndQuota.downPercentInfo}>
                                    <InfoCircleOutlined />
                                </Tooltip>
                                :
                            </label>
                            <InputNumber
                                min={0}
                                value={globalDownPercent}
                                onChange={(val) => setGlobalDownPercent(val || 0)}
                                style={{ marginRight: 24 }}
                            />
                            <Button onClick={handleSetAllDownPercent}>
                                {language.warningAndQuota.setAllDownPercentButton}
                            </Button>
                        </div>
                    </div>

                    {/* 表格 */}
                    <Table
                        columns={quotaColumns}
                        dataSource={quotaData.map((row, idx) => ({ ...row, key: idx }))}
                        pagination={false}
                        style={{ marginBottom: 24 }}
                    />
                </>
            )}

            {quotaMode === "confidence" && (
                <>
                    <div style={{ marginBottom: 24 }}>
                        <label style={{ marginRight: 12 }}>
                            {language.warningAndQuota.confidenceLabel}{" "}
                            <Tooltip title={language.warningAndQuota.confidenceInfo}>
                                <InfoCircleOutlined />
                            </Tooltip>
                            :
                        </label>
                        <InputNumber
                            min={0}
                            max={100}
                            value={confidence}
                            onChange={(val) => setConfidence(val || 95)}
                            style={{ marginRight: 24 }}
                        />
                        <Button onClick={handleSetConfidence}>
                            {language.warningAndQuota.setConfidenceButton}
                        </Button>
                    </div>

                    <Table
                        columns={confidenceColumns}
                        dataSource={confidenceData.map((row, idx) => ({
                            ...row,
                            key: idx,
                        }))}
                        pagination={false}
                        style={{ marginBottom: 24 }}
                    />
                </>
            )}

            {quotaMode === "disabled" && <div style={{ marginBottom: 24 }} />}

            {/* 提交按钮 */}
            <div style={{ textAlign: "right" }}>
                <Button type="primary" onClick={handleSubmit}>
                    {language.warningAndQuota.submitButton}
                </Button>
            </div>
            <Modal
                title={language.warningAndQuota.submitConfirmTitle}
                open={isSubmitting}
                onOk={handleModalOk}
                onCancel={handleModalCancel}
                footer={[
                    <Button key="cancel" onClick={handleModalCancel}>
                        {language.warningAndQuota.submitConfirmCancel}
                    </Button>,
                    <Button key="ok" type="primary" onClick={handleModalOk}>
                        {language.warningAndQuota.submitConfirmOk}
                    </Button>,
                ]}
            >
                <Table
                    columns={[
                        {
                            title: language.warningAndQuota.changedPresetName,
                            dataIndex: "presetName",
                        },
                    ]}
                    dataSource={[{ key: 1, presetName: selectedPreset }]}
                    pagination={false}
                    size="small"
                />
            </Modal>
        </div>

    );
};
