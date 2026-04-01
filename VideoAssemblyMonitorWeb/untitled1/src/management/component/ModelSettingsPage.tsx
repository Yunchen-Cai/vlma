//
// ModelSettingsPage.tsx
//
// 为不同Preset选择使用不同的模型进行计算
//

import React, {useEffect, useState} from "react";
import {Table, Button, Modal, message, Select} from "antd";
import { useLanguage } from "../../LanguageContext";
import { Typography } from 'antd';
import {fetchModels, getAllConfigs, updateUseModelPreset} from "../services/configAPI.ts";
import {host} from "../../Share.tsx";

const { Title } = Typography;

interface PresetModelData {
    key: string;
    name: string;
    currentModel: string;
}

export const ModelSettingsPage: React.FC = () => {
    const { language } = useLanguage();
    // 示例数据
    const [data, setData] = useState<PresetModelData[]>([
        { key: "1", name: "Preset1", currentModel: "Eoid" },
        { key: "2", name: "Preset2", currentModel: "Yolo" },
        { key: "3", name: "Preset3", currentModel: "" },
    ]);
    // 选中的行
    const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
    // 应用模型时，弹窗中显示的变更信息
    const [applyModalVisible, setApplyModalVisible] = useState<boolean>(false);
    const [applyChanges, setApplyChanges] = useState<
        { presetName: string; oldModel: string; newModel: string }[]
    >([]);

    const [modelList, setModelList] = useState<string[]>([]);
    const [selectedModel, setSelectedModel] = useState<string>("");


    useEffect(() => {
        const fetchPresets = () => {
            getAllConfigs().then(async (configs) => {
                console.log(configs);
                const useModel = configs.useModel;
                try {
                    const response = await fetch(host + "/all-preset");

                    if (!response.ok) {
                        // 如果返回码不是 200~299，抛出异常
                        console.error(`HTTP error! status: ${response.status}`);
                    }
                    // 后端返回的是 List<String>，解析为 string[]
                    const data: string[] = await response.json();

                    for (const datum of data) {
                        if (!(datum in useModel)) {
                            useModel[datum] = useModel["default"]
                        }
                    }
                    const newData: PresetModelData[] = [];
                    let i = 1
                    for (const useModelKey in useModel) {
                        newData.push({
                            key: i.toString(), name: useModelKey, currentModel: useModel[useModelKey]
                        } as PresetModelData)
                        i++;
                    }
                    setData(newData);
                } catch (error) {
                    console.error("Failed to fetch presets:", error);
                }
            });
            fetchModels().then((models)=>{
                if (models == undefined) return;
                setModelList(models);
                if (models.length > 0 && selectedModel === "") {
                    setSelectedModel(models[0]); // 默认选中第一个模型
                }
            })
        }
        fetchPresets();

        const intervalId = setInterval(fetchPresets, 1000);

        // 组件卸载时清除定时器
        return () => {
            clearInterval(intervalId);
        };

    }, [selectedModel]);

    // 选择行
    const rowSelection = {
        selectedRowKeys,
        onChange: (newSelectedRowKeys: React.Key[]) => {
            setSelectedRowKeys(newSelectedRowKeys);
        },
    };

    const columns = [
        {
            title: language.model.tablePresetName,
            dataIndex: "name",
            key: "name",
        },
        {
            title: language.model.tableCurrentModel,
            dataIndex: "currentModel",
            key: "currentModel",
        },
    ];

    const handleSelectAll = () => {
        const allKeys = data.map((item) => item.key);
        setSelectedRowKeys(allKeys);
    };

    const handleInvertSelect = () => {
        const newSelected = data
            .filter((d) => !selectedRowKeys.includes(d.key))
            .map((d) => d.key);
        setSelectedRowKeys(newSelected);
    };


    // 当下拉框改变时
    const handleModelSelect = (value: string) => {
        setSelectedModel(value);
    };

    // 应用所选模型到所有选中的预设
    const handleApplyModel = () => {
        if (selectedRowKeys.length === 0) {
            message.warning(language.model.noPresetSelected);
            return;
        }
        const changes = data
            .filter((d) => selectedRowKeys.includes(d.key))
            .map((d) => ({
                presetName: d.name,
                oldModel: d.currentModel,
                newModel: selectedModel,
            }));
        setApplyChanges(changes);
        setApplyModalVisible(true);
    };

    const applyModalColumns = [
        {
            title: language.model.changedPresetName,
            dataIndex: "presetName",
            key: "presetName",
        },
        {
            title: language.model.oldModel,
            dataIndex: "oldModel",
            key: "oldModel",
        },
        {
            title: language.model.newModel,
            dataIndex: "newModel",
            key: "newModel",
        },
    ];

    // 确认更新：调用后端接口
    const handleApplyModalOk = async () => {
        try {
            // 批量更新后端
            for (const change of applyChanges) {
                await updateUseModelPreset(change.presetName, change.newModel);
            }
            // 更新本地数据
            const updatedData = data.map((item) => {
                const change = applyChanges.find((c) => c.presetName === item.name);
                if (change) {
                    return { ...item, currentModel: change.newModel };
                }
                return item;
            });
            setData(updatedData);
            setApplyModalVisible(false);
            message.success("Model changes applied successfully!");
        } catch (err) {
            message.error("Failed to update model: " + String(err));
        }
    };


    const handleApplyModalCancel = () => {
        setApplyModalVisible(false);
    };

    return (
        <div style={{ marginTop: 36, padding: "24px 60px", gap:"16px" }}>
            <Title>{language.model.pageTitle}</Title>

            <div style={{ marginBottom: 12, marginTop: 48 }}>
                <Button onClick={handleSelectAll} style={{ marginRight: 24 }}>
                    {language.model.selectAllButton}
                </Button>
                <Button onClick={handleInvertSelect} style={{ marginRight: 24 }}>
                    {language.model.invertSelectButton}
                </Button>
                <span>{language.model.applyModelPrompt}</span>
                <Select
                    placeholder={language.model.selectModelPlaceholder}
                    value={selectedModel}
                    onChange={handleModelSelect}
                    style={{ width: 400, marginLeft: 8, marginRight: 8 }}
                >
                    {modelList.map((model) => (
                        <Select.Option key={model} value={model}>
                            {model}
                        </Select.Option>
                    ))}
                </Select>
                <Button onClick={handleApplyModel}>
                    {language.model.applyButton}
                </Button>
            </div>

            <Table
                rowSelection={rowSelection}
                columns={columns}
                dataSource={data}
                pagination={false}
                style={{ marginBottom: 24 }}
            />

            <Modal
                title={language.model.applyConfirmTitle}
                open={applyModalVisible}
                onOk={handleApplyModalOk}
                onCancel={handleApplyModalCancel}
                okText={language.model.applyConfirmOk}
                cancelText={language.model.applyConfirmCancel}
            >
                <Table
                    columns={applyModalColumns}
                    dataSource={applyChanges.map((c, idx) => ({ ...c, key: idx }))}
                    pagination={false}
                    size="small"
                />
            </Modal>
        </div>
    );
};
