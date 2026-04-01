// noinspection JSUnusedGlobalSymbols

import { useEffect, useState } from "react";
import { Table } from "antd";
import { host } from "../../Share.tsx";
import { useLanguage } from "../../LanguageContext.tsx";  // <== 引入多语言上下文
import { Preset } from "../entity/Preset.ts";
import { PresetNode } from "../entity/PresetNode.ts";

function PresetTable() {
    const [presetData, setPresetData] = useState<Preset[]>([]);
    const { language } = useLanguage();
    // language 即当前语言的文案对象，包含 presetTable.columns.* 等

    useEffect(() => {
        // 获取 /all-preset-obj 接口的数据
        fetch(host + "/all-preset-obj")
            .then((response) => response.json())
            .then((data) => {
                setPresetData(data);
            })
            .catch((error) => {
                console.error("获取 Preset 数据失败：", error);
            });
    }, []);

    // 顶层（Preset）列定义：使用 language.presetTable?.columns.xxx
    const presetColumns = [
        {
            title: language.presetTable?.columns.presetId || "Preset ID",
            dataIndex: "id",
            key: "id",
            width: 120,
        },
        {
            title: language.presetTable?.columns.presetName || "Preset 名称",
            dataIndex: "name",
            key: "name",
        },
    ];

    // 二级（Node）列定义
    const nodeColumns = [
        {
            title: language.presetTable?.columns.nodeNumber || "Node Number",
            key: "number",
            render: (_: string, record: PresetNode) => record.id.number,
            width: 120,
        },
        {
            title: language.presetTable?.columns.nodeName || "Node 名称",
            dataIndex: "name",
            key: "name",
        },
        {
            title: language.presetTable?.columns.realQuota || "Real Quota",
            dataIndex: "real_quota",
            key: "realQuota",
            width: 120,
        },
        {
            title: language.presetTable?.columns.rank || "Rank",
            dataIndex: "rank",
            key: "rank",
            width: 80,
        },
        {
            title: language.presetTable?.columns.actions || "Actions",
            dataIndex: "actions",
            key: "actions",
            // actions 通常是一个字符串数组，这里简单用逗号拼起来
            render: (actions: string[]) => actions && actions.join(", "),
        },
        {
            title: language.presetTable?.columns.parents || "父节点(Names)",
            key: "parents",
            render: (_: string, record: PresetNode) => {
                if (record.parents && record.parents.length > 0) {
                    return record.parents.map((p) => p.name).join(", ");
                }
                return "";
            },
        },
    ];

    return (
        <Table
            // 顶层表格使用预设数据
            columns={presetColumns}
            dataSource={presetData}
            rowKey={(record) => record.id} // Preset 的 id
            pagination={false} // 不分页
            style={{ width: "100%", height: "100%" }}
            expandable={{
                // 展开行中嵌套子表格，展示每个 preset 的节点
                expandedRowRender: (record) => (
                    <Table
                        columns={nodeColumns}
                        dataSource={record.nodes}
                        rowKey={(node) => `${node.id.preset}-${node.id.number}`} // Node 的复合主键
                        pagination={false}
                    />
                ),
                // 当 nodes 有内容时才允许展开
                rowExpandable: (record) =>
                    Array.isArray(record.nodes) && record.nodes.length > 0,
            }}
        />
    );
}

export default PresetTable;
