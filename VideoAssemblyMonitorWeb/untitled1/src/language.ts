//
// language.tsx
//
// 用于统一管理多语言文本内容
//

export interface TextInterface {
    common: {
        s: string;
        noData: string;
        title: string;
        languageSelectLabel: string;
        languageSelectPlaceholder: string;
        restartBackendLabel: string;
        closeBackendLabel: string;
        restartBackendConfirmTitle: string;
        closeBackendConfirmTitle: string;
        confirmOk: string;
        confirmCancel: string;

        // New fields for messages / placeholders:
        languageChangedMessage: string;
        restartingBackendMessage: string;
        closingBackendMessage: string;
        loadingChart: string;
    };

    menu: {
        systemStatus: string;
        database: string;
        workLog: string;
        preset: string;
        settings: string;
    };

    systemStatus: {
        cpuUsage: string;
        systemMemory: string;
        totalMemory: string;
        usedMemory: string;
        diskUsage: string;
        diskTotal: string;
        diskUsed: string;
        jvmHeap: string;
        maxHeapMemory: string;
        usedHeapMemory: string;
        jvmThreads: string;
        activeThreadCount: string;
        peakThreadCount: string;
        jvmClassLoading: string;
        loadedClassCount: string;
        totalLoadedClassCount: string;
        unloadedClassCount: string;
    };

    network: {
        submit: string;
        pageTitle: string;
        managementHostLabel: string;
        managementPortLabel: string;
        eoidHostLabel: string;
        eoidPortLabel: string;
        roboflowHostLabel: string;
        roboflowPortLabel: string;
        testButton: string;
    };

    warningAndQuota: {
        pageTitle: string;
        presetSelectLabel: string;
        presetSelectAll: string;
        calculateStatsButton: string;
        calculateStatsModalTitle: string;
        stepColumn: string;
        averageTimeColumn: string;
        stdDevColumn: string;
        quotaModeSelectLabel: string;
        quotaModeAvgOffset: string;
        quotaModeConfidence: string;
        quotaModeDisabled: string;
        importAvgTimeButton: string;
        importAvgTimeDisabledTip: string;
        upPercentLabel: string;
        downPercentLabel: string;
        setAllUpPercentButton: string;
        setAllDownPercentButton: string;
        upPercentInfo: string;
        downPercentInfo: string;
        confidenceLabel: string;
        confidenceInfo: string;
        setConfidenceButton: string;
        acceptanceUpper: string;
        acceptanceLower: string;
        quotaTime: string;
        upBoundaryTime: string;
        downBoundaryTime: string;
        submitButton: string;
        submitConfirmTitle: string;
        submitConfirmOk: string;
        submitConfirmCancel: string;
        changedPresetName: string;
    };

    model: {
        pageTitle: string;
        selectAllButton: string;
        invertSelectButton: string;
        applyEoidButton: string;
        applyYoloButton: string;
        applyConfirmTitle: string;
        applyConfirmOk: string;
        applyConfirmCancel: string;
        tablePresetName: string;
        tableCurrentModel: string;
        modelEoid: string;
        modelYolo: string;
        changedPresetName: string;
        oldModel: string;
        newModel: string;
        applyModelPrompt: string;
        selectModelPlaceholder: string;
        applyButton: string;
        noPresetSelected: string;
    };

    // New block for the “Review” or “Log” table and timeline
    review: {
        tableHeaders: {
            id: string;
            operator: string;
            preset: string;
            startTime: string;
            endTime: string;
            duration: string;
            observations: string;
            viewInChart: string;
        };
        timeline: {
            summaryExplanation: string;
            blueGreenExplanation: string;
            standardProgressExplanation: string;
            offsetProgressExplanation: string;
            progressExplanationTitle: string;
            exportBackgroundGraphMessage: string;
            exportToPDF: string;
            procNotFound: string;
            totalTimeout: string;
            modelStandardBounds: string;
            modelStandardTime: string;
            realWorkTime: string;
            wholeTimeFromOffsetStart: string;
            offsetQuotaWithHandling: string;
            realWorkInOffsetDuration: string;
            wholeTimeFromStandardStart: string;
            standardQuotaWithHandling: string;
            realWorkInStandardDuration: string;
            reportTitle: string;
            reportDataTitle: string;
            titlePrefix: string;     // e.g. "Timeline for "
            rawData: string;
            filteredData: string;
            offsetQuota: string;
            realWork: string;
            standardQuota: string;
            logNoPrefix: string;     // e.g. "Log No."
            orderIsAcceptable: string;
            orderIsNotAcceptable: string;
            executionOrderLabel: string;
        };
    };

    presetTable?: {
        columns: {
            presetId: string;
            presetName: string;
            nodeNumber: string;
            nodeName: string;
            realQuota: string;
            rank: string;
            actions: string;
            parents: string;
        };
    };
}

// 示例中文文案
export const ChineseText: TextInterface = {
    presetTable: {
        columns: {
            presetId: "Preset ID",
            presetName: "Preset 名称",
            nodeNumber: "Node 编号",
            nodeName: "Node 名称",
            realQuota: "配额时间",
            rank: "排序等级",
            actions: "可用操作",
            parents: "父节点(Names)",
        }
    },
    common: {
        title: "通用",
        languageSelectLabel: "选择语言",
        languageSelectPlaceholder: "请选择语言",
        restartBackendLabel: "重启后端服务器",
        closeBackendLabel: "关闭后端服务器",
        restartBackendConfirmTitle: "确认要重启后端服务器吗？",
        closeBackendConfirmTitle: "确认要关闭后端服务器吗？",
        confirmOk: "确定",
        confirmCancel: "取消",

        // new
        languageChangedMessage: "语言已切换到: ",
        restartingBackendMessage: "正在重启后端服务器...",
        closingBackendMessage: "正在关闭后端服务器...",
        loadingChart: "图表加载中...",
        noData: "没有数据",
        s: "秒"
    },
    systemStatus: {
        cpuUsage: "CPU 使用率",
        systemMemory: "系统内存使用",
        totalMemory: "总内存",
        usedMemory: "已使用内存",
        diskUsage: "磁盘使用",
        diskTotal: "磁盘总容量",
        diskUsed: "已使用磁盘",
        jvmHeap: "JVM Heap 使用",
        maxHeapMemory: "最大堆内存",
        usedHeapMemory: "已使用堆内存",
        jvmThreads: "JVM 线程信息",
        activeThreadCount: "当前活动线程数",
        peakThreadCount: "峰值线程数",
        jvmClassLoading: "JVM 类加载信息",
        loadedClassCount: "当前已加载类总数",
        totalLoadedClassCount: "历史总加载过的类数量",
        unloadedClassCount: "已卸载的类数量",
    },
    menu: {
        systemStatus: "系统状态",
        database: "数据库",
        workLog: "工作日志",
        preset: "预置",
        settings: "设置"
    },
    network: {
        pageTitle: "网络设置",
        managementHostLabel: "管理界面 Host",
        managementPortLabel: "管理界面 Port",
        eoidHostLabel: "Eoid Host",
        eoidPortLabel: "Eoid Port",
        roboflowHostLabel: "Roboflow Host",
        roboflowPortLabel: "Roboflow Port",
        testButton: "测试",
        submit: "应用"
    },
    warningAndQuota: {
        pageTitle: "警告与工时配额设置",
        presetSelectLabel: "选择要配置的 Preset",
        presetSelectAll: "应用到所有 Preset",
        calculateStatsButton: "计算平均时间/标准差",
        calculateStatsModalTitle: "工步平均时间与标准差",
        stepColumn: "工步",
        averageTimeColumn: "平均时间",
        stdDevColumn: "时间标准差",
        quotaModeSelectLabel: "选择 Quota 模式",
        quotaModeAvgOffset: "平均时间指定偏移",
        quotaModeConfidence: "置信度假设检验",
        quotaModeDisabled: "关闭警告",
        importAvgTimeButton: "导入计算的平均时间",
        importAvgTimeDisabledTip: "请先计算平均时间",
        upPercentLabel: "上移百分比",
        downPercentLabel: "下移百分比",
        setAllUpPercentButton: "提交上移百分比",
        setAllDownPercentButton: "提交下移百分比",
        upPercentInfo: "上移百分比用于计算超时上界",
        downPercentInfo: "下移百分比用于计算超时下界",
        confidenceLabel: "设置置信度",
        confidenceInfo: "根据置信度计算工步时间接受区间",
        setConfidenceButton: "提交置信度",
        acceptanceUpper: "接受上界",
        acceptanceLower: "接受下界",
        quotaTime: "配额时间",
        upBoundaryTime: "上界(时间)",
        downBoundaryTime: "下界(时间)",
        submitButton: "提交",
        submitConfirmTitle: "确认提交对以下 Preset 的修改？",
        submitConfirmOk: "确认",
        submitConfirmCancel: "取消",
        changedPresetName: "Preset 名称",
    },
    model: {
        pageTitle: "模型选择设置",
        selectAllButton: "全选",
        invertSelectButton: "反选",
        applyEoidButton: "应用到 Eoid",
        applyYoloButton: "应用到 YOLO",
        applyConfirmTitle: "确认对以下 Preset 修改模型？",
        applyConfirmOk: "确认",
        applyConfirmCancel: "取消",
        tablePresetName: "Preset 名称",
        tableCurrentModel: "当前模型",
        modelEoid: "Eoid",
        modelYolo: "Yolo",
        changedPresetName: "Preset 名称",
        oldModel: "原模型",
        newModel: "新模型",
        applyModelPrompt: "将所有选中的预设使用的模型修改为：",
        selectModelPlaceholder: "选择模型",
        applyButton: "提交",
        noPresetSelected: "未选中预设"
    },
    review: {
        tableHeaders: {
            id: "ID",
            operator: "操作员",
            preset: "预置",
            startTime: "开始时间",
            endTime: "结束时间",
            duration: "持续时间",
            observations: "观察",
            viewInChart: "查看图表"
        },
        timeline: {
            titlePrefix: "时间线 - ",
            rawData: "原始数据",
            filteredData: "过滤后数据",
            offsetQuota: "偏移配额",
            realWork: "真实工作",
            standardQuota: "标准配额",
            logNoPrefix: "日志编号 ",
            reportTitle: "工作记录报告",
            reportDataTitle: "数据报告",
            totalTimeout: "总超时",
            modelStandardBounds: "模型标准边界",
            modelStandardTime: "模型标准时间",
            realWorkTime: "实际工作时间",
            wholeTimeFromOffsetStart: "从偏置开始点计算的整体工序时间",
            offsetQuotaWithHandling: "附加有Handling时间的偏置定额工时",
            realWorkInOffsetDuration: "在偏置整体工序时间中的实际工作时间",
            wholeTimeFromStandardStart: "从标准开始点计算的整体工序时间",
            standardQuotaWithHandling: "附加有Handling时间的标准定额工时",
            realWorkInStandardDuration: "在标准整体工序时间中的实际工作时间",
            procNotFound: "未找到该工序",
            orderIsAcceptable: "顺序可接受",
            orderIsNotAcceptable: "顺序不符合",
            executionOrderLabel: "执行顺序：",
            exportToPDF: "导出到PDF",
            exportBackgroundGraphMessage: "导出时，请勾选 \"背景图形\"",
            progressExplanationTitle: "进度条说明",
            offsetProgressExplanation: "1. 偏移进度条：\n" +
                "蓝色部分：表示在 \"偏移\" 时间段内实际工作的进展。此为在 \"偏移配额\" 期间实际工作的时间，不包括任何处理或延迟。\n" +
                "绿色部分：表示在 \"标准\" 配额期间实际工作的进展。绿色部分反映了与节点标准配额相比已完成的工作量。绿色部分越大，过程越接近满足标准配额。",
            standardProgressExplanation: "2. 标准进度条：\n" +
                "蓝色部分：表示在节点的标准配额期间实际工作的进展。与偏移进度条的蓝色部分类似，但着重于标准配额的时间。\n" +
                "绿色部分：表示在预期或计算配额内完成的工作量，考虑到处理时间。这是通过已完成的工作总时长和总标准配额计算的，包括处理或额外时间的调整。",
            blueGreenExplanation: "指标与含义：\n" +
                "蓝色部分（在偏移和标准进度条中）提供了关于已完成所需工作的视觉提示，仅考虑落在 \"实际\" 工作时间内的工作部分。\n" +
                "绿色部分显示相对于整体预期时间（无论是节点的标准配额还是偏移配额）已完成的工作量。绿色部分越大，表示过程按预期或 \"标准\" 进度推进，而较小或缺失的绿色部分则可能表示延迟或低效。",
            summaryExplanation: "总结：\n" +
                "蓝色部分：显示在相应配额期间完成的工作。\n" +
                "绿色部分：显示在计算的配额内完成的工作量，表明效率和与预期的一致性。\n" +
                "通过跟踪这些颜色段，报告提供了关于每个节点在工作流中的时间和效率的见解。"
        }
    }
};

export const TraditionalChineseText: TextInterface = {
    presetTable: {
        columns: {
            presetId: "Preset ID",
            presetName: "Preset 名稱",
            nodeNumber: "Node 編號",
            nodeName: "Node 名稱",
            realQuota: "配額時間",
            rank: "排序等級",
            actions: "可用操作",
            parents: "父節點(Names)",
        }
    },
    common: {
        title: "通用",
        languageSelectLabel: "選擇語言",
        languageSelectPlaceholder: "請選擇語言",
        restartBackendLabel: "重啟後端服務器",
        closeBackendLabel: "關閉後端服務器",
        restartBackendConfirmTitle: "確認要重啟後端服務器嗎？",
        closeBackendConfirmTitle: "確認要關閉後端服務器嗎？",
        confirmOk: "確定",
        confirmCancel: "取消",

        // new
        languageChangedMessage: "語言已切換到：",
        restartingBackendMessage: "正在重啟後端服務器...",
        closingBackendMessage: "正在關閉後端服務器...",
        loadingChart: "圖表加載中...",
        noData: "沒有數據",
        s: "秒"
    },
    systemStatus: {
        cpuUsage: "CPU 使用率",
        systemMemory: "系統記憶體使用",
        totalMemory: "總記憶體",
        usedMemory: "已使用記憶體",
        diskUsage: "磁碟使用",
        diskTotal: "磁碟總容量",
        diskUsed: "已使用磁碟",
        jvmHeap: "JVM Heap 使用",
        maxHeapMemory: "最大堆記憶體",
        usedHeapMemory: "已使用堆記憶體",
        jvmThreads: "JVM 線程資訊",
        activeThreadCount: "當前活動線程數",
        peakThreadCount: "峰值線程數",
        jvmClassLoading: "JVM 類別載入資訊",
        loadedClassCount: "當前已載入類別總數",
        totalLoadedClassCount: "歷史總載入過的類別數量",
        unloadedClassCount: "已卸載的類別數量",
    },
    menu: {
        systemStatus: "系統狀態",
        database: "資料庫",
        workLog: "工作日誌",
        preset: "預置",
        settings: "設定"
    },
    network: {
        pageTitle: "網路設定",
        managementHostLabel: "管理介面 Host",
        managementPortLabel: "管理介面 Port",
        eoidHostLabel: "Eoid Host",
        eoidPortLabel: "Eoid Port",
        roboflowHostLabel: "Roboflow Host",
        roboflowPortLabel: "Roboflow Port",
        testButton: "測試",
        submit: "應用"
    },
    warningAndQuota: {
        pageTitle: "警告與工時配額設定",
        presetSelectLabel: "選擇要配置的 Preset",
        presetSelectAll: "應用到所有 Preset",
        calculateStatsButton: "計算平均時間/標準差",
        calculateStatsModalTitle: "工步平均時間與標準差",
        stepColumn: "工步",
        averageTimeColumn: "平均時間",
        stdDevColumn: "時間標準差",
        quotaModeSelectLabel: "選擇 Quota 模式",
        quotaModeAvgOffset: "平均時間指定偏移",
        quotaModeConfidence: "信賴度假設檢驗",
        quotaModeDisabled: "關閉警告",
        importAvgTimeButton: "匯入計算的平均時間",
        importAvgTimeDisabledTip: "請先計算平均時間",
        upPercentLabel: "上移百分比",
        downPercentLabel: "下移百分比",
        setAllUpPercentButton: "提交上移百分比",
        setAllDownPercentButton: "提交下移百分比",
        upPercentInfo: "上移百分比用於計算超時上界",
        downPercentInfo: "下移百分比用於計算超時下界",
        confidenceLabel: "設定信賴度",
        confidenceInfo: "根據信賴度計算工步時間接受區間",
        setConfidenceButton: "提交信賴度",
        acceptanceUpper: "接受上界",
        acceptanceLower: "接受下界",
        quotaTime: "配額時間",
        upBoundaryTime: "上界(時間)",
        downBoundaryTime: "下界(時間)",
        submitButton: "提交",
        submitConfirmTitle: "確認提交對以下 Preset 的修改？",
        submitConfirmOk: "確認",
        submitConfirmCancel: "取消",
        changedPresetName: "Preset 名稱",
    },
    model: {
        pageTitle: "模型選擇設定",
        selectAllButton: "全選",
        invertSelectButton: "反選",
        applyEoidButton: "應用到 Eoid",
        applyYoloButton: "應用到 YOLO",
        applyConfirmTitle: "確認對以下 Preset 修改模型？",
        applyConfirmOk: "確認",
        applyConfirmCancel: "取消",
        tablePresetName: "Preset 名稱",
        tableCurrentModel: "當前模型",
        modelEoid: "Eoid",
        modelYolo: "Yolo",
        changedPresetName: "Preset 名稱",
        oldModel: "原模型",
        newModel: "新模型",
        applyModelPrompt: "將所有選中的預設使用的模型修改為：",
        selectModelPlaceholder: "選擇模型",
        applyButton: "提交",
        noPresetSelected: "未選中預設"
    },
    review: {
        tableHeaders: {
            id: "ID",
            operator: "操作員",
            preset: "預置",
            startTime: "開始時間",
            endTime: "結束時間",
            duration: "持續時間",
            observations: "觀察",
            viewInChart: "查看圖表"
        },
        timeline: {
            titlePrefix: "時間線 - ",
            rawData: "原始資料",
            filteredData: "過濾後資料",
            offsetQuota: "偏移配額",
            realWork: "真實工作",
            standardQuota: "標準配額",
            logNoPrefix: "日誌編號 ",
            reportTitle: "工作記錄報告",
            reportDataTitle: "資料報告",
            totalTimeout: "總超時",
            modelStandardBounds: "模型標準邊界",
            modelStandardTime: "模型標準時間",
            realWorkTime: "實際工作時間",
            wholeTimeFromOffsetStart: "從偏置開始點計算的整體工序時間",
            offsetQuotaWithHandling: "附加有Handling時間的偏置定額工時",
            realWorkInOffsetDuration: "在偏置整體工序時間中的實際工作時間",
            wholeTimeFromStandardStart: "從標準開始點計算的整體工序時間",
            standardQuotaWithHandling: "附加有Handling時間的標準定額工時",
            realWorkInStandardDuration: "在標準整體工序時間中的實際工作時間",
            procNotFound: "未找到該工序",
            orderIsAcceptable: "順序可接受",
            orderIsNotAcceptable: "順序不符合",
            executionOrderLabel: "執行順序：",
            exportToPDF: "匯出為 PDF",
            exportBackgroundGraphMessage: "導出時，請勾選 \"背景圖\" 復選框。",
            progressExplanationTitle: "進度條說明",
            offsetProgressExplanation: "1. 偏移進度條：\n" +
                "藍色部分：表示在 \"偏移\" 時間段內實際工作的進展。此為在 \"偏移配額\" 期間實際工作的時間，不包括任何處理或延遲。\n" +
                "綠色部分：表示在 \"標準\" 配額期間實際工作的進展。綠色部分反映了與節點標準配額相比已完成的工作量。綠色部分越大，過程越接近滿足標準配額。",
            standardProgressExplanation: "2. 標準進度條：\n" +
                "藍色部分：表示在節點的標準配額期間實際工作的進展。與偏移進度條的藍色部分類似，但著重於標準配額的時間。\n" +
                "綠色部分：表示在預期或計算配額內完成的工作量，考慮到處理時間。這是通過已完成的工作總時長和總標準配額計算的，包括處理或額外時間的調整。",
            blueGreenExplanation: "指標與含義：\n" +
                "藍色部分（在偏移和標準進度條中）提供了關於已完成所需工作的視覺提示，僅考慮落在 \"實際\" 工作時間內的工作部分。\n" +
                "綠色部分顯示相對於整體預期時間（無論是節點的標準配額還是偏移配額）已完成的工作量。綠色部分越大，表示過程按預期或 \"標準\" 進度推進，而較小或缺失的綠色部分則可能表示延遲或低效。",
            summaryExplanation: "總結：\n" +
                "藍色部分：顯示在相應配額期間完成的工作。\n" +
                "綠色部分：顯示在計算的配額內完成的工作量，表明效率和與預期的一致性。\n" +
                "通過跟蹤這些顏色段，報告提供了關於每個節點在工作流中的時間和效率的見解。"
        }
    }
};

export const EnglishText: TextInterface = {
    presetTable: {
        columns: {
            presetId: "Preset ID",
            presetName: "Preset Name",
            nodeNumber: "Node Number",
            nodeName: "Node Name",
            realQuota: "Real Quota",
            rank: "Rank",
            actions: "Actions",
            parents: "Parent Nodes",
        }
    },
    common: {
        title: "General",
        languageSelectLabel: "Language",
        languageSelectPlaceholder: "Select language",
        restartBackendLabel: "Restart Backend",
        closeBackendLabel: "Close Backend",
        restartBackendConfirmTitle: "Confirm to restart the backend?",
        closeBackendConfirmTitle: "Confirm to close the backend?",
        confirmOk: "OK",
        confirmCancel: "Cancel",

        // new
        languageChangedMessage: "Language changed to: ",
        restartingBackendMessage: "Restarting backend server...",
        closingBackendMessage: "Closing backend server...",
        loadingChart: "Loading Chart...",
        noData: "No Data",
        s: "s"
    },
    systemStatus: {
        cpuUsage: "CPU Usage",
        systemMemory: "System Memory Usage",
        totalMemory: "Total Memory",
        usedMemory: "Used Memory",
        diskUsage: "Disk Usage",
        diskTotal: "Total Disk Capacity",
        diskUsed: "Used Disk",
        jvmHeap: "JVM Heap Usage",
        maxHeapMemory: "Max Heap Memory",
        usedHeapMemory: "Used Heap Memory",
        jvmThreads: "JVM Threads Info",
        activeThreadCount: "Active Thread Count",
        peakThreadCount: "Peak Thread Count",
        jvmClassLoading: "JVM Class Loading Info",
        loadedClassCount: "Loaded Class Count",
        totalLoadedClassCount: "Total Loaded Class Count",
        unloadedClassCount: "Unloaded Class Count",
    },
    menu: {
        systemStatus: "System Status",
        database: "Database",
        workLog: "Work Log",
        preset: "Preset",
        settings: "Settings"
    },
    network: {
        pageTitle: "Network",
        managementHostLabel: "Management Host",
        managementPortLabel: "Management Port",
        eoidHostLabel: "Eoid Host",
        eoidPortLabel: "Eoid Port",
        roboflowHostLabel: "Roboflow Host",
        roboflowPortLabel: "Roboflow Port",
        testButton: "Test",
        submit: "apply",
    },
    warningAndQuota: {
        pageTitle: "Warning & Quota",
        presetSelectLabel: "Select a Preset",
        presetSelectAll: "Apply to All Presets",
        calculateStatsButton: "Calculate Average/StdDev",
        calculateStatsModalTitle: "Steps Average Time & StdDev",
        stepColumn: "Step",
        averageTimeColumn: "Average Time",
        stdDevColumn: "StdDev",
        quotaModeSelectLabel: "Select Quota Mode",
        quotaModeAvgOffset: "Average Time with Offset",
        quotaModeConfidence: "Confidence Hypothesis Test",
        quotaModeDisabled: "Disable Warning",
        importAvgTimeButton: "Import Calculated Average Time",
        importAvgTimeDisabledTip: "Please calculate first",
        upPercentLabel: "Up Shift (%)",
        downPercentLabel: "Down Shift (%)",
        setAllUpPercentButton: "Submit Up Shift",
        setAllDownPercentButton: "Submit Down Shift",
        upPercentInfo: "Up shift percent used to compute upper boundary",
        downPercentInfo: "Down shift percent used to compute lower boundary",
        confidenceLabel: "Set Confidence",
        confidenceInfo: "Compute acceptance interval by confidence",
        setConfidenceButton: "Submit Confidence",
        acceptanceUpper: "Upper Bound",
        acceptanceLower: "Lower Bound",
        quotaTime: "Quota Time",
        upBoundaryTime: "Upper (Time)",
        downBoundaryTime: "Lower (Time)",
        submitButton: "Submit",
        submitConfirmTitle: "Confirm to submit changes to these Presets?",
        submitConfirmOk: "OK",
        submitConfirmCancel: "Cancel",
        changedPresetName: "Preset Name",
    },
    model: {
        pageTitle: "Model",
        selectAllButton: "Select All",
        invertSelectButton: "Invert Selection",
        applyEoidButton: "Apply to Eoid",
        applyYoloButton: "Apply to YOLO",
        applyConfirmTitle: "Confirm to change models for these Presets?",
        applyConfirmOk: "OK",
        applyConfirmCancel: "Cancel",
        tablePresetName: "Preset Name",
        tableCurrentModel: "Current Model",
        modelEoid: "Eoid",
        modelYolo: "Yolo",
        changedPresetName: "Preset Name",
        oldModel: "Old Model",
        newModel: "New Model",
        applyModelPrompt: "Change the model for all selected presets to:",
        selectModelPlaceholder: "Select a model",
        applyButton: "Apply",
        noPresetSelected: "No Preset selected"
    },
    review: {
        tableHeaders: {
            id: "ID",
            operator: "Operator",
            preset: "Preset",
            startTime: "Start Time",
            endTime: "End Time",
            duration: "Duration",
            observations: "Observations",
            viewInChart: "View In Chart"
        },
        timeline: {
            titlePrefix: "Timeline for ",
            rawData: "Raw Data",
            filteredData: "Filtered Data",
            offsetQuota: "Offset Quota",
            realWork: "Real Work",
            standardQuota: "Standard Quota",
            logNoPrefix: "Log No.",
            reportTitle: "Report",
            reportDataTitle: "Report Data",
            totalTimeout: "Total Timeout",
            modelStandardBounds: "modelStandardBounds",
            modelStandardTime: "modelStandardTime",
            realWorkTime: "realWorkTime",
            wholeTimeFromOffsetStart: "wholeTimeFromOffsetStart",
            offsetQuotaWithHandling: "offsetQuotaWithHandling",
            realWorkInOffsetDuration: "realWorkInOffsetDuration",
            wholeTimeFromStandardStart: "wholeTimeFromStandardStart",
            standardQuotaWithHandling: "standardQuotaWithHandling",
            realWorkInStandardDuration: "realWorkInStandardDuration",
            procNotFound: "timeAnalysis of this procedure Not Found",
            orderIsAcceptable: "Order Acceptable",
            orderIsNotAcceptable: "Order Not Acceptable",
            executionOrderLabel: "Execution Order: ",
            exportToPDF: "export to PDF",
            exportBackgroundGraphMessage: "Please check the \"Background Graph\" when exporting.",
            progressExplanationTitle: "Progress Bar Explanation",
            offsetProgressExplanation: "1. Offset Progress Bar:\n" +
                "Blue portion: Represents the progress of the real work that occurs during the \"Offset\" time segment. This is the time spent working on the node during its \"offset quota\" period, excluding any handling or delays.\n" +
                "Green portion: Indicates the progress of the real work that happens within the \"Standard\" quota period. The green portion reflects the amount of work done compared to the standard quota for the node. The higher the green portion, the closer the process is to meeting the standard quota.",
            standardProgressExplanation: "2. Standard Progress Bar:\n" +
                "Blue portion: Represents the progress of real work during the standard quota period for the node. This is similar to the blue part of the Offset bar but focuses on the standard quota time.\n" +
                "Green portion: Indicates how much of the work has been completed within the expected or calculated quota, factoring in the handling time. This is calculated using the total duration of work done and the total standard quota, including adjustments for handling or extra time.",
            blueGreenExplanation: "Indicators and Meaning:\n" +
                "Blue segments (in both the Offset and Standard progress bars) provide a visual cue of how much of the required work has been done, considering only the work portion that falls within the \"actual\" work time.\n" +
                "Green segments show how much work has been completed, relative to the overall expected time (whether the node's standard quota or offset quota). A larger green segment means the process is progressing according to the expected or \"standard\" rate, whereas smaller or missing green segments may indicate delays or inefficiency.",
            summaryExplanation: "Summary:\n" +
                "Blue Sections: Show work done during the respective quota period.\n" +
                "Green Sections: Show how much of the work has been completed within the calculated quota, indicating efficiency and alignment with expectations.\n" +
                "By tracking these colored segments, the report provides insights into both the timing and efficiency of the assembly process for each node in the workflow."


        }
    }
};

export const JapaneseText: TextInterface = {
    common: {
        title: "全般",
        languageSelectLabel: "言語",
        languageSelectPlaceholder: "言語を選択",
        restartBackendLabel: "バックエンドを再起動",
        closeBackendLabel: "バックエンドを停止",
        restartBackendConfirmTitle: "バックエンドを再起動しますか？",
        closeBackendConfirmTitle: "バックエンドを停止しますか？",
        confirmOk: "OK",
        confirmCancel: "キャンセル",
        languageChangedMessage: "言語を切り替えました: ",
        restartingBackendMessage: "バックエンドを再起動しています...",
        closingBackendMessage: "バックエンドを停止しています...",
        loadingChart: "チャートを読み込み中...",
        noData: "データなし",
        s: "秒"
    },
    menu: {
        systemStatus: "システムステータス",
        database: "データベース",
        workLog: "作業ログ",
        preset: "プリセット",
        settings: "設定"
    },
    systemStatus: {
        cpuUsage: "CPU 使用率",
        systemMemory: "システムメモリ使用量",
        totalMemory: "総メモリ",
        usedMemory: "使用済メモリ",
        diskUsage: "ディスク使用量",
        diskTotal: "ディスク総容量",
        diskUsed: "使用済ディスク",
        jvmHeap: "JVM ヒープ使用",
        maxHeapMemory: "最大ヒープメモリ",
        usedHeapMemory: "使用中ヒープメモリ",
        jvmThreads: "JVM スレッド情報",
        activeThreadCount: "アクティブスレッド数",
        peakThreadCount: "ピークスレッド数",
        jvmClassLoading: "JVM クラスロード情報",
        loadedClassCount: "現在ロードされているクラス数",
        totalLoadedClassCount: "これまでロードされたクラス数",
        unloadedClassCount: "アンロードされたクラス数"
    },
    network: {
        submit: "適用",
        pageTitle: "ネットワーク設定",
        managementHostLabel: "管理ホスト",
        managementPortLabel: "管理ポート",
        eoidHostLabel: "Eoid ホスト",
        eoidPortLabel: "Eoid ポート",
        roboflowHostLabel: "Roboflow ホスト",
        roboflowPortLabel: "Roboflow ポート",
        testButton: "テスト"
    },
    warningAndQuota: {
        pageTitle: "警告と工時配額",
        presetSelectLabel: "プリセットを選択",
        presetSelectAll: "すべてのプリセットに適用",
        calculateStatsButton: "平均/標準偏差を計算",
        calculateStatsModalTitle: "工步平均時間と標準偏差",
        stepColumn: "工程ステップ",
        averageTimeColumn: "平均時間",
        stdDevColumn: "標準偏差",
        quotaModeSelectLabel: "Quotaモードを選択",
        quotaModeAvgOffset: "平均時間 + オフセット",
        quotaModeConfidence: "信頼度による検定",
        quotaModeDisabled: "警告を無効化",
        importAvgTimeButton: "計算した平均時間をインポート",
        importAvgTimeDisabledTip: "先に平均時間を計算してください",
        upPercentLabel: "上方シフト (%)",
        downPercentLabel: "下方シフト (%)",
        setAllUpPercentButton: "上方シフトを適用",
        setAllDownPercentButton: "下方シフトを適用",
        upPercentInfo: "上方シフト率は上限時間を計算するために使用",
        downPercentInfo: "下方シフト率は下限時間を計算するために使用",
        confidenceLabel: "信頼度設定",
        confidenceInfo: "信頼度に基づき受容区間を計算",
        setConfidenceButton: "設定を適用",
        acceptanceUpper: "受容上限",
        acceptanceLower: "受容下限",
        quotaTime: "配額時間",
        upBoundaryTime: "上限(時間)",
        downBoundaryTime: "下限(時間)",
        submitButton: "送信",
        submitConfirmTitle: "これらのプリセット変更を送信しますか？",
        submitConfirmOk: "OK",
        submitConfirmCancel: "キャンセル",
        changedPresetName: "プリセット名"
    },
    model: {
        pageTitle: "モデル設定",
        selectAllButton: "すべて選択",
        invertSelectButton: "選択を反転",
        applyEoidButton: "Eoidに適用",
        applyYoloButton: "YOLOに適用",
        applyConfirmTitle: "これらのプリセットのモデルを変更しますか？",
        applyConfirmOk: "OK",
        applyConfirmCancel: "キャンセル",
        tablePresetName: "プリセット名",
        tableCurrentModel: "現在のモデル",
        modelEoid: "Eoid",
        modelYolo: "Yolo",
        changedPresetName: "プリセット名",
        oldModel: "旧モデル",
        newModel: "新モデル",
        applyModelPrompt: "選択されたプリセットのモデルを変更：",
        selectModelPlaceholder: "モデルを選択",
        applyButton: "適用",
        noPresetSelected: "プリセットが選択されていません"
    },
    review: {
        tableHeaders: {
            id: "ID",
            operator: "オペレーター",
            preset: "プリセット",
            startTime: "開始時刻",
            endTime: "終了時刻",
            duration: "作業時間",
            observations: "観察",
            viewInChart: "チャートで表示"
        },
        timeline: {
            procNotFound: "該当工序が見つかりません",
            totalTimeout: "合計タイムアウト",
            modelStandardBounds: "モデル標準境界",
            modelStandardTime: "モデル標準時間",
            realWorkTime: "実作業時間",
            wholeTimeFromOffsetStart: "オフセット開始からの全作業時間",
            offsetQuotaWithHandling: "Handling含むオフセット定額時間",
            realWorkInOffsetDuration: "オフセット期間内の実作業時間",
            wholeTimeFromStandardStart: "標準開始からの全作業時間",
            standardQuotaWithHandling: "Handling含む標準定額時間",
            realWorkInStandardDuration: "標準期間内の実作業時間",
            reportTitle: "レポート",
            reportDataTitle: "レポートデータ",
            titlePrefix: "タイムライン - ",
            rawData: "生データ",
            filteredData: "フィルタ後データ",
            offsetQuota: "オフセット配額",
            realWork: "実際の作業",
            standardQuota: "標準配額",
            logNoPrefix: "ログ No.",
            orderIsAcceptable: "順序可",
            orderIsNotAcceptable: "順序不可",
            executionOrderLabel: "実行順序：",
            exportToPDF: "PDFにエクスポート",
            exportBackgroundGraphMessage: "エクスポート時に「背景グラフ」のチェックボックスを選択してください。",
            progressExplanationTitle: "進捗バーの説明",
            offsetProgressExplanation: "1. オフセット進捗バー：\n" +
                "青色部分：\"オフセット\" 時間帯内で実際に行われた作業の進捗を示します。これは \"オフセット配分\" 期間中の作業時間で、処理や遅延は含まれません。\n" +
                "緑色部分：\"標準\" 配分期間内で行われた実作業の進捗を示します。緑色部分は、ノードの標準配分と比較してどれだけ作業が進んだかを示します。緑色部分が大きいほど、プロセスが標準配分に近づいています。",
            standardProgressExplanation: "2. 標準進捗バー：\n" +
                "青色部分：ノードの標準配分期間中の実際の作業の進捗を示します。これはオフセットバーの青色部分に似ていますが、標準配分の時間に焦点を当てています。\n" +
                "緑色部分：予想または計算された配分内で完了した作業量を示します。処理時間も考慮に入れます。これは、完了した作業の合計時間と標準配分を使って計算されます。",
            blueGreenExplanation: "指標と意味：\n" +
                "青色部分（オフセットおよび標準進捗バーの両方）は、実際の作業時間内で完了した作業量を示す視覚的な手がかりを提供します。\n" +
                "緑色部分は、全体の予想時間（ノードの標準配分またはオフセット配分）に対してどれだけ作業が完了したかを示します。緑色部分が大きければ、プロセスは予想通りまたは「標準」通りに進んでいます。小さかったり、欠けている場合は、遅延や非効率を示しているかもしれません。",
            summaryExplanation: "要約：\n" +
                "青色部分：それぞれの配分期間中で完了した作業量を示します。\n" +
                "緑色部分：計算された配分内で完了した作業量を示し、効率と予想との一致を示します。\n" +
                "これらの色分けされたセグメントを追跡することによって、レポートは各ノードのワークフロー内での時間と効率に関する洞察を提供します。"


        }
    }
};


export const FrenchText: TextInterface = {
    common: {
        title: "Général",
        languageSelectLabel: "Langue",
        languageSelectPlaceholder: "Choisir la langue",
        restartBackendLabel: "Redémarrer le backend",
        closeBackendLabel: "Arrêter le backend",
        restartBackendConfirmTitle: "Confirmer le redémarrage du backend ?",
        closeBackendConfirmTitle: "Confirmer l'arrêt du backend ?",
        confirmOk: "OK",
        confirmCancel: "Annuler",
        languageChangedMessage: "Langue changée en : ",
        restartingBackendMessage: "Redémarrage du serveur backend...",
        closingBackendMessage: "Fermeture du serveur backend...",
        loadingChart: "Chargement du graphique...",
        noData: "Pas de données",
        s: "s"
    },
    menu: {
        systemStatus: "État du système",
        database: "Base de données",
        workLog: "Journal de travail",
        preset: "Préréglage",
        settings: "Paramètres"
    },
    systemStatus: {
        cpuUsage: "Utilisation du CPU",
        systemMemory: "Utilisation de la mémoire système",
        totalMemory: "Mémoire totale",
        usedMemory: "Mémoire utilisée",
        diskUsage: "Utilisation du disque",
        diskTotal: "Capacité totale du disque",
        diskUsed: "Disque utilisé",
        jvmHeap: "Utilisation du heap JVM",
        maxHeapMemory: "Mémoire max du heap",
        usedHeapMemory: "Mémoire utilisée du heap",
        jvmThreads: "Informations des threads JVM",
        activeThreadCount: "Nombre de threads actifs",
        peakThreadCount: "Nombre maximal de threads",
        jvmClassLoading: "Informations de chargement de classes JVM",
        loadedClassCount: "Nombre de classes chargées",
        totalLoadedClassCount: "Nombre total de classes chargées",
        unloadedClassCount: "Nombre de classes déchargées"
    },
    network: {
        submit: "Appliquer",
        pageTitle: "Réseau",
        managementHostLabel: "Hôte de gestion",
        managementPortLabel: "Port de gestion",
        eoidHostLabel: "Hôte Eoid",
        eoidPortLabel: "Port Eoid",
        roboflowHostLabel: "Hôte Roboflow",
        roboflowPortLabel: "Port Roboflow",
        testButton: "Tester"
    },
    warningAndQuota: {
        pageTitle: "Avertissement & Quota",
        presetSelectLabel: "Sélectionner un préréglage",
        presetSelectAll: "Appliquer à tous les préréglages",
        calculateStatsButton: "Calculer Moyenne/Écart-type",
        calculateStatsModalTitle: "Temps moyen & Écart-type des étapes",
        stepColumn: "Étape",
        averageTimeColumn: "Temps moyen",
        stdDevColumn: "Écart-type",
        quotaModeSelectLabel: "Choisir le mode Quota",
        quotaModeAvgOffset: "Temps moyen avec offset",
        quotaModeConfidence: "Test d'hypothèse de confiance",
        quotaModeDisabled: "Désactiver l'avertissement",
        importAvgTimeButton: "Importer la moyenne calculée",
        importAvgTimeDisabledTip: "Veuillez calculer d'abord",
        upPercentLabel: "Décalage vers le haut (%)",
        downPercentLabel: "Décalage vers le bas (%)",
        setAllUpPercentButton: "Valider le décalage haut",
        setAllDownPercentButton: "Valider le décalage bas",
        upPercentInfo: "Le décalage haut est utilisé pour calculer la limite supérieure",
        downPercentInfo: "Le décalage bas est utilisé pour calculer la limite inférieure",
        confidenceLabel: "Définir la confiance",
        confidenceInfo: "Calculer l'intervalle d'acceptation selon la confiance",
        setConfidenceButton: "Valider la confiance",
        acceptanceUpper: "Limite supérieure",
        acceptanceLower: "Limite inférieure",
        quotaTime: "Temps de quota",
        upBoundaryTime: "Limite haute (Temps)",
        downBoundaryTime: "Limite basse (Temps)",
        submitButton: "Soumettre",
        submitConfirmTitle: "Confirmer l'envoi des modifications pour ces préréglages ?",
        submitConfirmOk: "OK",
        submitConfirmCancel: "Annuler",
        changedPresetName: "Nom du préréglage"
    },
    model: {
        pageTitle: "Modèle",
        selectAllButton: "Tout sélectionner",
        invertSelectButton: "Inverser la sélection",
        applyEoidButton: "Appliquer à Eoid",
        applyYoloButton: "Appliquer à YOLO",
        applyConfirmTitle: "Confirmer la modification du modèle pour ces préréglages ?",
        applyConfirmOk: "OK",
        applyConfirmCancel: "Annuler",
        tablePresetName: "Nom du préréglage",
        tableCurrentModel: "Modèle actuel",
        modelEoid: "Eoid",
        modelYolo: "Yolo",
        changedPresetName: "Nom du préréglage",
        oldModel: "Ancien modèle",
        newModel: "Nouveau modèle",
        applyModelPrompt: "Changer le modèle pour tous les préréglages sélectionnés en :",
        selectModelPlaceholder: "Choisir un modèle",
        applyButton: "Appliquer",
        noPresetSelected: "Aucun préréglage sélectionné"
    },
    review: {
        tableHeaders: {
            id: "ID",
            operator: "Opérateur",
            preset: "Préréglage",
            startTime: "Heure de début",
            endTime: "Heure de fin",
            duration: "Durée",
            observations: "Observations",
            viewInChart: "Voir dans le graphique"
        },
        timeline: {
            procNotFound: "Procédure introuvable",
            totalTimeout: "Dépassement total",
            modelStandardBounds: "Limites standard du modèle",
            modelStandardTime: "Temps standard du modèle",
            realWorkTime: "Temps de travail réel",
            wholeTimeFromOffsetStart: "Durée totale depuis le début de l'offset",
            offsetQuotaWithHandling: "Quota offset incluant temps de handling",
            realWorkInOffsetDuration: "Temps de travail réel pendant la période offset",
            wholeTimeFromStandardStart: "Durée totale depuis le début du standard",
            standardQuotaWithHandling: "Quota standard incluant temps de handling",
            realWorkInStandardDuration: "Temps de travail réel pendant la période standard",
            reportTitle: "Rapport",
            reportDataTitle: "Données du rapport",
            titlePrefix: "Chronologie - ",
            rawData: "Données brutes",
            filteredData: "Données filtrées",
            offsetQuota: "Quota offset",
            realWork: "Travail réel",
            standardQuota: "Quota standard",
            logNoPrefix: "Log n°",
            orderIsAcceptable: "Ordre acceptable",
            orderIsNotAcceptable: "Ordre non acceptable",
            executionOrderLabel: "Ordre d'exécution : ",
            exportToPDF: "exporter au format PDF",
            exportBackgroundGraphMessage: "Veuillez cocher la case \"Graphique d'arrière-plan\" lors de l'exportation.",
            progressExplanationTitle: "Explication de la barre de progression",
            offsetProgressExplanation: "1. Barre de progression Offset :\n" +
                "La portion bleue : Représente la progression du travail réel effectué pendant la période \"Offset\". C'est le temps passé à travailler sur le nœud pendant sa période de \"quota offset\", excluant les retards ou les traitements.\n" +
                "La portion verte : Indique la progression du travail réel effectué pendant la période du \"Quota Standard\". La portion verte reflète la quantité de travail effectuée par rapport au quota standard du nœud. Plus la portion verte est grande, plus le processus se rapproche de l'atteinte du quota standard.",
            standardProgressExplanation: "2. Barre de progression Standard :\n" +
                "La portion bleue : Représente la progression du travail réel effectué pendant la période du quota standard pour le nœud. Cela ressemble à la portion bleue de la barre Offset mais se concentre sur le temps de quota standard.\n" +
                "La portion verte : Indique combien de travail a été réalisé dans le quota calculé ou attendu, en tenant compte du temps de traitement. Cela est calculé en utilisant la durée totale du travail effectué et le quota standard total, y compris les ajustements pour le traitement ou les temps supplémentaires.",
            blueGreenExplanation: "Indicateurs et Signification :\n" +
                "Les segments bleus (dans les barres de progression Offset et Standard) fournissent un indice visuel de la quantité de travail effectuée, en tenant compte uniquement du travail effectué dans la \"période de travail réelle\".\n" +
                "Les segments verts montrent combien de travail a été effectué par rapport à l'ensemble du temps prévu (qu'il s'agisse du quota standard ou du quota offset). Un plus grand segment vert signifie que le processus avance selon le taux prévu ou \"standard\", tandis que des segments verts plus petits ou manquants peuvent indiquer des retards ou une inefficacité.",
            summaryExplanation: "Résumé :\n" +
                "Les sections bleues : Montrent le travail effectué pendant la période de quota respective.\n" +
                "Les sections vertes : Montrent combien de travail a été effectué dans le quota calculé, indiquant l'efficacité et l'alignement avec les attentes.\n" +
                "En suivant ces segments colorés, le rapport fournit des informations sur le temps et l'efficacité du processus d'assemblage pour chaque nœud dans le flux de travail."


        }
    }
};


export const GermanText: TextInterface = {
    common: {
        title: "Allgemein",
        languageSelectLabel: "Sprache",
        languageSelectPlaceholder: "Sprache auswählen",
        restartBackendLabel: "Backend neu starten",
        closeBackendLabel: "Backend beenden",
        restartBackendConfirmTitle: "Backend wirklich neu starten?",
        closeBackendConfirmTitle: "Backend wirklich beenden?",
        confirmOk: "OK",
        confirmCancel: "Abbrechen",
        languageChangedMessage: "Sprache gewechselt zu: ",
        restartingBackendMessage: "Backend-Server wird neu gestartet...",
        closingBackendMessage: "Backend-Server wird beendet...",
        loadingChart: "Diagramm wird geladen...",
        noData: "Keine Daten",
        s: "s"
    },
    menu: {
        systemStatus: "Systemstatus",
        database: "Datenbank",
        workLog: "Arbeitsprotokoll",
        preset: "Voreinstellung",
        settings: "Einstellungen"
    },
    systemStatus: {
        cpuUsage: "CPU-Auslastung",
        systemMemory: "Systemspeicher-Auslastung",
        totalMemory: "Gesamtspeicher",
        usedMemory: "Genutzter Speicher",
        diskUsage: "Festplattennutzung",
        diskTotal: "Gesamte Festplattenkapazität",
        diskUsed: "Genutzte Festplatte",
        jvmHeap: "JVM Heap-Auslastung",
        maxHeapMemory: "Max. Heap-Speicher",
        usedHeapMemory: "Genutzter Heap-Speicher",
        jvmThreads: "JVM Thread-Informationen",
        activeThreadCount: "Aktive Thread-Anzahl",
        peakThreadCount: "Maximale Thread-Anzahl",
        jvmClassLoading: "JVM Klassenlade-Informationen",
        loadedClassCount: "Aktuell geladene Klassen",
        totalLoadedClassCount: "Insgesamt geladene Klassen",
        unloadedClassCount: "Entladene Klassen"
    },
    network: {
        submit: "Anwenden",
        pageTitle: "Netzwerkeinstellungen",
        managementHostLabel: "Management-Host",
        managementPortLabel: "Management-Port",
        eoidHostLabel: "Eoid-Host",
        eoidPortLabel: "Eoid-Port",
        roboflowHostLabel: "Roboflow-Host",
        roboflowPortLabel: "Roboflow-Port",
        testButton: "Testen"
    },
    warningAndQuota: {
        pageTitle: "Warnungen & Zeitarbeitskontingent",
        presetSelectLabel: "Voreinstellung auswählen",
        presetSelectAll: "Auf alle Voreinstellungen anwenden",
        calculateStatsButton: "Mittelwert/StdAbw berechnen",
        calculateStatsModalTitle: "Durchschnittliche Schrittzeiten & Standardabweichung",
        stepColumn: "Schritt",
        averageTimeColumn: "Durchschnittszeit",
        stdDevColumn: "Standardabweichung",
        quotaModeSelectLabel: "Quota-Modus wählen",
        quotaModeAvgOffset: "Durchschnittszeit mit Offset",
        quotaModeConfidence: "Konfidenztest",
        quotaModeDisabled: "Warnung deaktivieren",
        importAvgTimeButton: "Berechnete Durchschnittszeit importieren",
        importAvgTimeDisabledTip: "Bitte zuerst berechnen",
        upPercentLabel: "Aufwärts-Verschiebung (%)",
        downPercentLabel: "Abwärts-Verschiebung (%)",
        setAllUpPercentButton: "Aufwärts-Verschiebung anwenden",
        setAllDownPercentButton: "Abwärts-Verschiebung anwenden",
        upPercentInfo: "Aufwärts-Verschiebung für obere Grenze",
        downPercentInfo: "Abwärts-Verschiebung für untere Grenze",
        confidenceLabel: "Konfidenz festlegen",
        confidenceInfo: "Akzeptanzintervall basierend auf Konfidenz berechnen",
        setConfidenceButton: "Konfidenz anwenden",
        acceptanceUpper: "Obere Akzeptanzgrenze",
        acceptanceLower: "Untere Akzeptanzgrenze",
        quotaTime: "Kontingentzeit",
        upBoundaryTime: "Obere Grenze (Zeit)",
        downBoundaryTime: "Untere Grenze (Zeit)",
        submitButton: "Senden",
        submitConfirmTitle: "Änderungen für diese Voreinstellungen wirklich übernehmen?",
        submitConfirmOk: "OK",
        submitConfirmCancel: "Abbrechen",
        changedPresetName: "Voreinstellungsname"
    },
    model: {
        pageTitle: "Modell",
        selectAllButton: "Alle auswählen",
        invertSelectButton: "Auswahl umkehren",
        applyEoidButton: "Auf Eoid anwenden",
        applyYoloButton: "Auf YOLO anwenden",
        applyConfirmTitle: "Modell für diese Voreinstellungen wirklich ändern?",
        applyConfirmOk: "OK",
        applyConfirmCancel: "Abbrechen",
        tablePresetName: "Voreinstellungsname",
        tableCurrentModel: "Aktuelles Modell",
        modelEoid: "Eoid",
        modelYolo: "Yolo",
        changedPresetName: "Voreinstellungsname",
        oldModel: "Altes Modell",
        newModel: "Neues Modell",
        applyModelPrompt: "Das Modell für alle ausgewählten Voreinstellungen ändern zu:",
        selectModelPlaceholder: "Modell auswählen",
        applyButton: "Anwenden",
        noPresetSelected: "Keine Voreinstellung ausgewählt"
    },
    review: {
        tableHeaders: {
            id: "ID",
            operator: "Bediener",
            preset: "Voreinstellung",
            startTime: "Startzeit",
            endTime: "Endzeit",
            duration: "Dauer",
            observations: "Beobachtungen",
            viewInChart: "Im Diagramm anzeigen"
        },
        timeline: {
            procNotFound: "Vorgang nicht gefunden",
            totalTimeout: "Gesamt-Timeout",
            modelStandardBounds: "Modell-Standardgrenzen",
            modelStandardTime: "Modell-Standardzeit",
            realWorkTime: "Reale Arbeitszeit",
            wholeTimeFromOffsetStart: "Gesamtzeit ab Offset-Start",
            offsetQuotaWithHandling: "Offset-Kontingent inkl. Handling-Zeit",
            realWorkInOffsetDuration: "Reale Arbeitszeit während Offset-Periode",
            wholeTimeFromStandardStart: "Gesamtzeit ab Standard-Start",
            standardQuotaWithHandling: "Standard-Kontingent inkl. Handling-Zeit",
            realWorkInStandardDuration: "Reale Arbeitszeit während Standard-Periode",
            reportTitle: "Bericht",
            reportDataTitle: "Berichtsdaten",
            titlePrefix: "Zeitplan - ",
            rawData: "Rohdaten",
            filteredData: "Gefilterte Daten",
            offsetQuota: "Offset-Kontingent",
            realWork: "Reale Arbeit",
            standardQuota: "Standard-Kontingent",
            logNoPrefix: "Protokoll Nr.",
            orderIsAcceptable: "Reihenfolge akzeptabel",
            orderIsNotAcceptable: "Reihenfolge nicht akzeptabel",
            executionOrderLabel: "Ausführungsreihenfolge: ",
            exportToPDF: "als PDF exportieren",
            exportBackgroundGraphMessage: "Bitte aktivieren Sie das Kontrollkästchen \"Hintergrunddiagramm\" beim Exportieren.",
            progressExplanationTitle: "Erklärung der Fortschrittsanzeige",
            offsetProgressExplanation: "1. Offset-Fortschrittsanzeige:\n" +
                "Blaue Portion: Repräsentiert den Fortschritt der tatsächlichen Arbeit, die während des \"Offset\"-Zeitraums geleistet wird. Dies ist die Zeit, die mit der Arbeit am Knoten während seines \"Offset-Quoten\"-Zeitraums verbracht wird, ohne Verzögerungen oder Bearbeitung.\n" +
                "Grüne Portion: Zeigt den Fortschritt der tatsächlichen Arbeit, die während des \"Standard\"-Quotenzeitraums erfolgt. Die grüne Portion spiegelt die Menge an Arbeit wider, die im Vergleich zum Standard-Quota des Knotens erledigt wurde. Je größer der grüne Anteil, desto näher ist der Prozess an der Erfüllung des Standard-Quotas.",
            standardProgressExplanation: "2. Standard-Fortschrittsanzeige:\n" +
                "Blaue Portion: Repräsentiert den Fortschritt der tatsächlichen Arbeit während des Standard-Quota-Zeitraums für den Knoten. Dies ist ähnlich wie die blaue Portion der Offset-Leiste, jedoch mit Fokus auf die Standard-Quota-Zeit.\n" +
                "Grüne Portion: Zeigt, wie viel Arbeit innerhalb des erwarteten oder berechneten Quotas abgeschlossen wurde, einschließlich der Bearbeitungszeit. Dies wird unter Verwendung der Gesamtarbeitsdauer und des gesamten Standard-Quotas berechnet, einschließlich Anpassungen für Bearbeitung oder zusätzliche Zeit.",
            blueGreenExplanation: "Indikatoren und Bedeutung:\n" +
                "Blaue Segmente (in beiden Fortschrittsanzeigen, Offset und Standard) bieten eine visuelle Hilfe, um anzuzeigen, wie viel der erforderlichen Arbeit erledigt wurde, wobei nur die Arbeit berücksichtigt wird, die innerhalb der \"tatsächlichen\" Arbeitszeit stattgefunden hat.\n" +
                "Grüne Segmente zeigen, wie viel Arbeit im Vergleich zur Gesamtzeit (ob Standard-Quota oder Offset-Quota) abgeschlossen wurde. Ein größerer grüner Abschnitt bedeutet, dass der Prozess gemäß dem erwarteten oder \"Standard\"-Tempo voranschreitet, während kleinere oder fehlende grüne Abschnitte auf Verzögerungen oder Ineffizienz hinweisen können.",
            summaryExplanation: "Zusammenfassung:\n" +
                "Blaue Abschnitte: Zeigen die Arbeit an, die während des jeweiligen Quotenzeitraums abgeschlossen wurde.\n" +
                "Grüne Abschnitte: Zeigen, wie viel Arbeit innerhalb des berechneten Quotas abgeschlossen wurde, was auf Effizienz und Übereinstimmung mit den Erwartungen hinweist.\n" +
                "Durch die Verfolgung dieser farbigen Abschnitte liefert der Bericht Einblicke in die Zeit und Effizienz des Montageprozesses für jeden Knoten im Workflow."


        }
    }
};

//////////////////////////////////////////////////////////////////////
// 俄语 (Russian)
//////////////////////////////////////////////////////////////////////
export const RussianText: TextInterface = {
    common: {
        title: "Общее",
        languageSelectLabel: "Язык",
        languageSelectPlaceholder: "Выберите язык",
        restartBackendLabel: "Перезапустить бэкенд",
        closeBackendLabel: "Остановить бэкенд",
        restartBackendConfirmTitle: "Действительно перезапустить бэкенд?",
        closeBackendConfirmTitle: "Действительно остановить бэкенд?",
        confirmOk: "OK",
        confirmCancel: "Отмена",
        languageChangedMessage: "Язык переключен на: ",
        restartingBackendMessage: "Перезапуск бэкенд-сервера...",
        closingBackendMessage: "Остановка бэкенд-сервера...",
        loadingChart: "Загрузка графика...",
        noData: "Нет данных",
        s: "с"
    },
    menu: {
        systemStatus: "Состояние системы",
        database: "База данных",
        workLog: "Журнал работы",
        preset: "Пресет",
        settings: "Настройки"
    },
    systemStatus: {
        cpuUsage: "Загрузка CPU",
        systemMemory: "Использование системной памяти",
        totalMemory: "Всего памяти",
        usedMemory: "Использовано памяти",
        diskUsage: "Использование диска",
        diskTotal: "Общий объём диска",
        diskUsed: "Использовано диска",
        jvmHeap: "Использование JVM Heap",
        maxHeapMemory: "Максимальная память Heap",
        usedHeapMemory: "Использованная память Heap",
        jvmThreads: "Информация о потоках JVM",
        activeThreadCount: "Количество активных потоков",
        peakThreadCount: "Пиковое количество потоков",
        jvmClassLoading: "Информация о загрузке классов JVM",
        loadedClassCount: "Загружено классов",
        totalLoadedClassCount: "Всего загруженных классов",
        unloadedClassCount: "Выгружено классов"
    },
    network: {
        submit: "Применить",
        pageTitle: "Сеть",
        managementHostLabel: "Управляющий хост",
        managementPortLabel: "Управляющий порт",
        eoidHostLabel: "Хост Eoid",
        eoidPortLabel: "Порт Eoid",
        roboflowHostLabel: "Хост Roboflow",
        roboflowPortLabel: "Порт Roboflow",
        testButton: "Тест"
    },
    warningAndQuota: {
        pageTitle: "Предупреждения и квота",
        presetSelectLabel: "Выберите пресет",
        presetSelectAll: "Применить ко всем пресетам",
        calculateStatsButton: "Вычислить среднее/ст. откл.",
        calculateStatsModalTitle: "Среднее время шагов и стандартное отклонение",
        stepColumn: "Шаг",
        averageTimeColumn: "Среднее время",
        stdDevColumn: "Стандартное отклонение",
        quotaModeSelectLabel: "Выберите режим квоты",
        quotaModeAvgOffset: "Среднее время + смещение",
        quotaModeConfidence: "Проверка гипотезы (доверие)",
        quotaModeDisabled: "Отключить предупреждение",
        importAvgTimeButton: "Импортировать вычисленное среднее",
        importAvgTimeDisabledTip: "Сначала выполните вычисление",
        upPercentLabel: "Смещение вверх (%)",
        downPercentLabel: "Смещение вниз (%)",
        setAllUpPercentButton: "Установить смещение вверх",
        setAllDownPercentButton: "Установить смещение вниз",
        upPercentInfo: "Используется для расчёта верхней границы",
        downPercentInfo: "Используется для расчёта нижней границы",
        confidenceLabel: "Задать доверие",
        confidenceInfo: "Рассчитать интервал приёмлемости на основе доверия",
        setConfidenceButton: "Применить доверие",
        acceptanceUpper: "Верхняя граница",
        acceptanceLower: "Нижняя граница",
        quotaTime: "Время квоты",
        upBoundaryTime: "Верхняя граница (время)",
        downBoundaryTime: "Нижняя граница (время)",
        submitButton: "Отправить",
        submitConfirmTitle: "Подтвердить изменения для данных пресетов?",
        submitConfirmOk: "OK",
        submitConfirmCancel: "Отмена",
        changedPresetName: "Имя пресета"
    },
    model: {
        pageTitle: "Модель",
        selectAllButton: "Выбрать все",
        invertSelectButton: "Инвертировать выбор",
        applyEoidButton: "Применить к Eoid",
        applyYoloButton: "Применить к YOLO",
        applyConfirmTitle: "Подтвердить изменение модели для этих пресетов?",
        applyConfirmOk: "OK",
        applyConfirmCancel: "Отмена",
        tablePresetName: "Имя пресета",
        tableCurrentModel: "Текущая модель",
        modelEoid: "Eoid",
        modelYolo: "Yolo",
        changedPresetName: "Имя пресета",
        oldModel: "Старая модель",
        newModel: "Новая модель",
        applyModelPrompt: "Изменить модель для всех выбранных пресетов на:",
        selectModelPlaceholder: "Выберите модель",
        applyButton: "Применить",
        noPresetSelected: "Не выбраны пресеты"
    },
    review: {
        tableHeaders: {
            id: "ID",
            operator: "Оператор",
            preset: "Пресет",
            startTime: "Время начала",
            endTime: "Время окончания",
            duration: "Продолжительность",
            observations: "Наблюдения",
            viewInChart: "Посмотреть на графике"
        },
        timeline: {
            procNotFound: "Процедура не найдена",
            totalTimeout: "Общий таймаут",
            modelStandardBounds: "Стандартные границы модели",
            modelStandardTime: "Стандартное время модели",
            realWorkTime: "Реальное рабочее время",
            wholeTimeFromOffsetStart: "Общее время с начала смещения",
            offsetQuotaWithHandling: "Квота со смещением (с учётом Handling)",
            realWorkInOffsetDuration: "Реальное рабочее время в периоде смещения",
            wholeTimeFromStandardStart: "Общее время с начала стандарта",
            standardQuotaWithHandling: "Стандартная квота (с учётом Handling)",
            realWorkInStandardDuration: "Реальное рабочее время в периоде стандарта",
            reportTitle: "Отчёт",
            reportDataTitle: "Данные отчёта",
            titlePrefix: "Таймлайн - ",
            rawData: "Исходные данные",
            filteredData: "Отфильтрованные данные",
            offsetQuota: "Квота со смещением",
            realWork: "Реальная работа",
            standardQuota: "Стандартная квота",
            logNoPrefix: "Журнал №",
            orderIsAcceptable: "Порядок приемлем",
            orderIsNotAcceptable: "Порядок неприемлем",
            executionOrderLabel: "Порядок выполнения: ",
            exportToPDF: "экспорт в PDF",
            exportBackgroundGraphMessage: "Пожалуйста, установите флажок \"Фоновая графика\" при экспорте.",
            progressExplanationTitle: "Пояснение к индикатору прогресса",
            offsetProgressExplanation: "1. Индикатор прогресса Offset:\n" +
                "Синяя часть: Представляет прогресс фактической работы, выполняемой в период \"Offset\". Это время, потраченное на работу с узлом в его периоде \"Offset квоты\", без учета обработки или задержек.\n" +
                "Зеленая часть: Указывает прогресс реальной работы, выполняемой в периоде \"Стандартной\" квоты. Зеленая часть отражает количество выполненной работы по сравнению со стандартной квотой для узла. Чем больше зеленая часть, тем ближе процесс к выполнению стандартной квоты.",
            standardProgressExplanation: "2. Индикатор прогресса Standard:\n" +
                "Синяя часть: Представляет прогресс фактической работы в периоде стандартной квоты для узла. Это похоже на синюю часть индикатора Offset, но с фокусом на стандартное время квоты.\n" +
                "Зеленая часть: Указывает, сколько работы было выполнено в пределах ожидаемой или вычисленной квоты, включая время на обработку. Это вычисляется с использованием общей продолжительности выполненной работы и общей стандартной квоты, включая корректировки для обработки или дополнительного времени.",
            blueGreenExplanation: "Индикаторы и их значение:\n" +
                "Синие сегменты (в обоих индикаторах, Offset и Standard) предоставляют визуальное представление о том, сколько работы было выполнено, с учетом только работы, которая была выполнена в \"реальное\" рабочее время.\n" +
                "Зеленые сегменты показывают, сколько работы было выполнено относительно общей ожидаемой времени (стандартной или offset квоты). Большая зеленая часть означает, что процесс продвигается в соответствии с ожидаемым или \"стандартным\" темпом, в то время как меньшие или отсутствующие зеленые сегменты могут указывать на задержки или неэффективность.",
            summaryExplanation: "Резюме:\n" +
                "Синие сегменты: Показывают выполненную работу в пределах соответствующего периода квоты.\n" +
                "Зеленые сегменты: Показывают, сколько работы было выполнено в пределах вычисленной квоты, что указывает на эффективность и соответствие ожиданиям.\n" +
                "Отслеживание этих цветных сегментов позволяет получать информацию о времени и эффективности процесса сборки для каждого узла в рабочем процессе."


        }
    }
};

//////////////////////////////////////////////////////////////////////
// 韩语 (Korean)
//////////////////////////////////////////////////////////////////////
export const KoreanText: TextInterface = {
    common: {
        title: "일반",
        languageSelectLabel: "언어",
        languageSelectPlaceholder: "언어 선택",
        restartBackendLabel: "백엔드 재시작",
        closeBackendLabel: "백엔드 종료",
        restartBackendConfirmTitle: "백엔드를 재시작하시겠습니까?",
        closeBackendConfirmTitle: "백엔드를 종료하시겠습니까?",
        confirmOk: "확인",
        confirmCancel: "취소",
        languageChangedMessage: "언어가 다음으로 변경됨: ",
        restartingBackendMessage: "백엔드 서버 재시작 중...",
        closingBackendMessage: "백엔드 서버 종료 중...",
        loadingChart: "차트 로딩 중...",
        noData: "데이터 없음",
        s: "초"
    },
    menu: {
        systemStatus: "시스템 상태",
        database: "데이터베이스",
        workLog: "작업 로그",
        preset: "프리셋",
        settings: "설정"
    },
    systemStatus: {
        cpuUsage: "CPU 사용량",
        systemMemory: "시스템 메모리 사용량",
        totalMemory: "전체 메모리",
        usedMemory: "사용 중인 메모리",
        diskUsage: "디스크 사용량",
        diskTotal: "디스크 총 용량",
        diskUsed: "디스크 사용 중",
        jvmHeap: "JVM 힙 사용",
        maxHeapMemory: "최대 힙 메모리",
        usedHeapMemory: "사용된 힙 메모리",
        jvmThreads: "JVM 스레드 정보",
        activeThreadCount: "활성 스레드 수",
        peakThreadCount: "최대 스레드 수",
        jvmClassLoading: "JVM 클래스 로딩 정보",
        loadedClassCount: "로드된 클래스 수",
        totalLoadedClassCount: "누적 로드된 클래스 수",
        unloadedClassCount: "언로드된 클래스 수"
    },
    network: {
        submit: "적용",
        pageTitle: "네트워크",
        managementHostLabel: "관리 호스트",
        managementPortLabel: "관리 포트",
        eoidHostLabel: "Eoid 호스트",
        eoidPortLabel: "Eoid 포트",
        roboflowHostLabel: "Roboflow 호스트",
        roboflowPortLabel: "Roboflow 포트",
        testButton: "테스트"
    },
    warningAndQuota: {
        pageTitle: "경고 및 작업 할당량",
        presetSelectLabel: "프리셋 선택",
        presetSelectAll: "모든 프리셋에 적용",
        calculateStatsButton: "평균/표준편차 계산",
        calculateStatsModalTitle: "단계 평균 시간 & 표준편차",
        stepColumn: "단계",
        averageTimeColumn: "평균 시간",
        stdDevColumn: "표준편차",
        quotaModeSelectLabel: "할당량 모드 선택",
        quotaModeAvgOffset: "평균 시간 + 오프셋",
        quotaModeConfidence: "신뢰도 가설 검정",
        quotaModeDisabled: "경고 비활성화",
        importAvgTimeButton: "계산된 평균 시간 가져오기",
        importAvgTimeDisabledTip: "먼저 평균 시간을 계산하세요",
        upPercentLabel: "상향 조정 (%)",
        downPercentLabel: "하향 조정 (%)",
        setAllUpPercentButton: "상향 조정 적용",
        setAllDownPercentButton: "하향 조정 적용",
        upPercentInfo: "상향 비율은 상한 시간 계산에 사용",
        downPercentInfo: "하향 비율은 하한 시간 계산에 사용",
        confidenceLabel: "신뢰도 설정",
        confidenceInfo: "신뢰도를 기반으로 수용 구간 계산",
        setConfidenceButton: "신뢰도 적용",
        acceptanceUpper: "상한",
        acceptanceLower: "하한",
        quotaTime: "할당 시간",
        upBoundaryTime: "상한(시간)",
        downBoundaryTime: "하한(시간)",
        submitButton: "제출",
        submitConfirmTitle: "이 프리셋들의 변경 사항을 제출하시겠습니까?",
        submitConfirmOk: "확인",
        submitConfirmCancel: "취소",
        changedPresetName: "프리셋 이름"
    },
    model: {
        pageTitle: "모델",
        selectAllButton: "전체 선택",
        invertSelectButton: "선택 반전",
        applyEoidButton: "Eoid에 적용",
        applyYoloButton: "YOLO에 적용",
        applyConfirmTitle: "이 프리셋들의 모델을 변경하시겠습니까?",
        applyConfirmOk: "확인",
        applyConfirmCancel: "취소",
        tablePresetName: "프리셋 이름",
        tableCurrentModel: "현재 모델",
        modelEoid: "Eoid",
        modelYolo: "Yolo",
        changedPresetName: "프리셋 이름",
        oldModel: "이전 모델",
        newModel: "새 모델",
        applyModelPrompt: "선택된 모든 프리셋의 모델을 변경:",
        selectModelPlaceholder: "모델 선택",
        applyButton: "적용",
        noPresetSelected: "선택된 프리셋이 없습니다"
    },
    review: {
        tableHeaders: {
            id: "ID",
            operator: "작업자",
            preset: "프리셋",
            startTime: "시작 시간",
            endTime: "종료 시간",
            duration: "지속 시간",
            observations: "관찰",
            viewInChart: "차트로 보기"
        },
        timeline: {
            procNotFound: "해당 공정을 찾을 수 없습니다",
            totalTimeout: "전체 타임아웃",
            modelStandardBounds: "모델 표준 경계",
            modelStandardTime: "모델 표준 시간",
            realWorkTime: "실제 작업 시간",
            wholeTimeFromOffsetStart: "오프셋 시작부터의 전체 시간",
            offsetQuotaWithHandling: "Handling이 포함된 오프셋 할당",
            realWorkInOffsetDuration: "오프셋 기간 중 실제 작업 시간",
            wholeTimeFromStandardStart: "표준 시작부터의 전체 시간",
            standardQuotaWithHandling: "Handling이 포함된 표준 할당",
            realWorkInStandardDuration: "표준 기간 중 실제 작업 시간",
            reportTitle: "보고서",
            reportDataTitle: "보고서 데이터",
            titlePrefix: "타임라인 - ",
            rawData: "원시 데이터",
            filteredData: "필터된 데이터",
            offsetQuota: "오프셋 할당",
            realWork: "실제 작업",
            standardQuota: "표준 할당",
            logNoPrefix: "로그 번호 ",
            orderIsAcceptable: "순서 허용",
            orderIsNotAcceptable: "순서 불가",
            executionOrderLabel: "실행 순서: ",
            exportToPDF: "PDF로 내보내기",
            exportBackgroundGraphMessage: "내보낼 때 \"배경 그래프\" 체크박스를 선택하세요.",
            progressExplanationTitle: "진행률 바 설명",
            offsetProgressExplanation: "1. 오프셋 진행률 바:\n" +
                "파란색 부분: \"오프셋\" 시간대 동안 실제 작업이 진행된 정도를 나타냅니다. 이는 \"오프셋 할당량\" 기간 동안 노드에서 수행한 작업 시간으로, 처리나 지연은 제외됩니다.\n" +
                "초록색 부분: \"표준\" 할당량 기간 동안 실제 작업의 진행 정도를 나타냅니다. 초록색 부분은 노드의 표준 할당량에 비례하여 완료된 작업 양을 나타냅니다. 초록색 부분이 클수록 프로세스가 표준 할당량을 충족하는 데 더 가까워집니다.",
            standardProgressExplanation: "2. 표준 진행률 바:\n" +
                "파란색 부분: 노드의 표준 할당량 기간 동안 실제 작업이 진행된 정도를 나타냅니다. 이는 오프셋 바의 파란색 부분과 유사하지만 표준 할당량 시간에 초점을 맞춥니다.\n" +
                "초록색 부분: 예상된 또는 계산된 할당량 내에서 완료된 작업량을 나타냅니다. 처리 시간을 포함하여 총 작업 시간과 총 표준 할당량을 사용하여 계산됩니다.",
            blueGreenExplanation: "지표 및 의미:\n" +
                "파란색 부분(오프셋 및 표준 진행률 바 모두)은 \"실제\" 작업 시간 내에서 완료된 작업량에 대한 시각적 단서를 제공합니다.\n" +
                "초록색 부분은 전체 예상 시간(표준 할당량 또는 오프셋 할당량)과 비교하여 완료된 작업량을 나타냅니다. 초록색 부분이 크면 프로세스가 예상된 또는 \"표준\" 속도로 진행되고 있다는 의미이며, 초록색 부분이 작거나 없으면 지연이나 비효율성을 나타낼 수 있습니다.",
            summaryExplanation: "요약:\n" +
                "파란색 부분: 해당 할당량 기간 동안 완료된 작업을 나타냅니다.\n" +
                "초록색 부분: 계산된 할당량 내에서 완료된 작업량을 나타내며, 효율성 및 예상과의 일치를 나타냅니다.\n" +
                "이 색상 구간을 추적하여 보고서는 각 노드의 작업 흐름에서 시간과 효율성에 대한 통찰력을 제공합니다."


        }
    }
};

//////////////////////////////////////////////////////////////////////
// 阿拉伯语 (Arabic)
//////////////////////////////////////////////////////////////////////
export const ArabicText: TextInterface = {
    common: {
        title: "عام",
        languageSelectLabel: "اللغة",
        languageSelectPlaceholder: "اختر اللغة",
        restartBackendLabel: "إعادة تشغيل الخادم الخلفي",
        closeBackendLabel: "إيقاف الخادم الخلفي",
        restartBackendConfirmTitle: "هل تريد إعادة تشغيل الخادم الخلفي؟",
        closeBackendConfirmTitle: "هل تريد إيقاف الخادم الخلفي؟",
        confirmOk: "نعم",
        confirmCancel: "إلغاء",
        languageChangedMessage: "تم تغيير اللغة إلى: ",
        restartingBackendMessage: "جاري إعادة تشغيل الخادم الخلفي...",
        closingBackendMessage: "جاري إيقاف الخادم الخلفي...",
        loadingChart: "جاري تحميل الرسم البياني...",
        noData: "لا توجد بيانات",
        s: "ث"
    },
    menu: {
        systemStatus: "حالة النظام",
        database: "قاعدة البيانات",
        workLog: "سجل العمل",
        preset: "الإعداد المسبق",
        settings: "الإعدادات"
    },
    systemStatus: {
        cpuUsage: "استخدام وحدة المعالجة المركزية",
        systemMemory: "استخدام ذاكرة النظام",
        totalMemory: "إجمالي الذاكرة",
        usedMemory: "الذاكرة المستخدمة",
        diskUsage: "استخدام القرص",
        diskTotal: "السعة الكلية للقرص",
        diskUsed: "القرص المستخدم",
        jvmHeap: "استخدام ذاكرة JVM Heap",
        maxHeapMemory: "أقصى ذاكرة Heap",
        usedHeapMemory: "الذاكرة Heap المستخدمة",
        jvmThreads: "معلومات خيوط JVM",
        activeThreadCount: "عدد الخيوط النشطة",
        peakThreadCount: "أقصى عدد من الخيوط",
        jvmClassLoading: "معلومات تحميل فئات JVM",
        loadedClassCount: "عدد الفئات المُحمّلة",
        totalLoadedClassCount: "مجموع الفئات التي تم تحميلها",
        unloadedClassCount: "الفئات المُفرغة"
    },
    network: {
        submit: "تطبيق",
        pageTitle: "الشبكة",
        managementHostLabel: "المضيف الإداري",
        managementPortLabel: "منفذ الإدارة",
        eoidHostLabel: "مضيف Eoid",
        eoidPortLabel: "منفذ Eoid",
        roboflowHostLabel: "مضيف Roboflow",
        roboflowPortLabel: "منفذ Roboflow",
        testButton: "اختبار"
    },
    warningAndQuota: {
        pageTitle: "التحذيرات والحصة",
        presetSelectLabel: "اختر إعدادًا مسبقًا",
        presetSelectAll: "تطبيق على جميع الإعدادات المسبقة",
        calculateStatsButton: "احسب المتوسط/الانحراف المعياري",
        calculateStatsModalTitle: "متوسط وقت الخطوات والانحراف المعياري",
        stepColumn: "الخطوة",
        averageTimeColumn: "متوسط الوقت",
        stdDevColumn: "الانحراف المعياري",
        quotaModeSelectLabel: "اختر وضع الحصة",
        quotaModeAvgOffset: "متوسط الوقت مع الإزاحة",
        quotaModeConfidence: "اختبار الثقة (اختبار الفرضية)",
        quotaModeDisabled: "تعطيل التحذير",
        importAvgTimeButton: "استيراد المتوسط المحسوب",
        importAvgTimeDisabledTip: "يرجى الحساب أولاً",
        upPercentLabel: "الإزاحة لأعلى (%)",
        downPercentLabel: "الإزاحة لأسفل (%)",
        setAllUpPercentButton: "تطبيق الإزاحة لأعلى",
        setAllDownPercentButton: "تطبيق الإزاحة لأسفل",
        upPercentInfo: "يُستخدم لحساب الحد الأعلى",
        downPercentInfo: "يُستخدم لحساب الحد الأدنى",
        confidenceLabel: "تعيين الثقة",
        confidenceInfo: "احسب نطاق القبول بناءً على الثقة",
        setConfidenceButton: "تطبيق الثقة",
        acceptanceUpper: "الحد الأعلى",
        acceptanceLower: "الحد الأدنى",
        quotaTime: "وقت الحصة",
        upBoundaryTime: "الحد الأعلى (الوقت)",
        downBoundaryTime: "الحد الأدنى (الوقت)",
        submitButton: "إرسال",
        submitConfirmTitle: "تأكيد إرسال التغييرات لهذه الإعدادات المسبقة؟",
        submitConfirmOk: "نعم",
        submitConfirmCancel: "إلغاء",
        changedPresetName: "اسم الإعداد المسبق"
    },
    model: {
        pageTitle: "النموذج",
        selectAllButton: "تحديد الكل",
        invertSelectButton: "عكس التحديد",
        applyEoidButton: "تطبيق على Eoid",
        applyYoloButton: "تطبيق على YOLO",
        applyConfirmTitle: "تأكيد تغيير النموذج لهذه الإعدادات المسبقة؟",
        applyConfirmOk: "نعم",
        applyConfirmCancel: "إلغاء",
        tablePresetName: "اسم الإعداد المسبق",
        tableCurrentModel: "النموذج الحالي",
        modelEoid: "Eoid",
        modelYolo: "Yolo",
        changedPresetName: "اسم الإعداد المسبق",
        oldModel: "النموذج القديم",
        newModel: "النموذج الجديد",
        applyModelPrompt: "تغيير النموذج لجميع الإعدادات المسبقة المختارة إلى:",
        selectModelPlaceholder: "اختر نموذجًا",
        applyButton: "تطبيق",
        noPresetSelected: "لم يتم اختيار أي إعداد مسبق"
    },
    review: {
        tableHeaders: {
            id: "المعرّف",
            operator: "المشغّل",
            preset: "الإعداد المسبق",
            startTime: "وقت البداية",
            endTime: "وقت النهاية",
            duration: "المدة",
            observations: "الملاحظات",
            viewInChart: "عرض في الرسم البياني"
        },
        timeline: {
            procNotFound: "الإجراء غير موجود",
            totalTimeout: "انتهاء المهلة الكلي",
            modelStandardBounds: "الحدود القياسية للنموذج",
            modelStandardTime: "الوقت القياسي للنموذج",
            realWorkTime: "وقت العمل الفعلي",
            wholeTimeFromOffsetStart: "الوقت الإجمالي منذ بدء الإزاحة",
            offsetQuotaWithHandling: "حصة الإزاحة (تشمل المعالجة)",
            realWorkInOffsetDuration: "العمل الفعلي خلال فترة الإزاحة",
            wholeTimeFromStandardStart: "الوقت الإجمالي منذ بدء المعيار",
            standardQuotaWithHandling: "حصة المعيار (تشمل المعالجة)",
            realWorkInStandardDuration: "العمل الفعلي خلال فترة المعيار",
            reportTitle: "تقرير",
            reportDataTitle: "بيانات التقرير",
            titlePrefix: "الجدول الزمني - ",
            rawData: "البيانات الأصلية",
            filteredData: "البيانات المصفاة",
            offsetQuota: "حصة الإزاحة",
            realWork: "العمل الفعلي",
            standardQuota: "الحصة القياسية",
            logNoPrefix: "السجل رقم ",
            orderIsAcceptable: "الترتيب مقبول",
            orderIsNotAcceptable: "الترتيب غير مقبول",
            executionOrderLabel: "ترتيب التنفيذ: ",
            exportToPDF: "التصدير إلى PDF",
            exportBackgroundGraphMessage: "يرجى تحديد مربع الاختيار \"الرسم البياني الخلفي\" عند التصدير.",
            progressExplanationTitle: "شرح شريط التقدم",
            offsetProgressExplanation: "1. شريط تقدم الإزاحة:\n" +
                "الجزء الأزرق: يمثل تقدم العمل الفعلي الذي يحدث خلال فترة \"الإزاحة\". هذا هو الوقت الذي تم قضاؤه في العمل على العقدة خلال فترة \"حصة الإزاحة\"، باستثناء أي تأخير أو معالجة.\n" +
                "الجزء الأخضر: يشير إلى تقدم العمل الفعلي الذي يحدث خلال فترة \"الحصة القياسية\". الجزء الأخضر يعكس كمية العمل المنجز مقارنة بالحصة القياسية للعقدة. كلما كانت المسافة الخضراء أكبر، كلما اقتربت العملية من تحقيق الحصة القياسية.",
            standardProgressExplanation: "2. شريط تقدم القياسي:\n" +
                "الجزء الأزرق: يمثل تقدم العمل الفعلي خلال فترة الحصة القياسية للعقدة. هذا يشبه الجزء الأزرق في شريط الإزاحة ولكن يركز على وقت الحصة القياسية.\n" +
                "الجزء الأخضر: يشير إلى مقدار العمل الذي تم إنجازه ضمن الحصة المتوقعة أو المحسوبة، مع مراعاة وقت المعالجة. يتم حساب هذا باستخدام إجمالي مدة العمل المنجز والإجمالي للحد الأدنى للوقت القياسي، بما في ذلك التعديلات للمعالجة أو الوقت الإضافي.",
            blueGreenExplanation: "المؤشرات والمعاني:\n" +
                "الأجزاء الزرقاء (في كلا من شريط الإزاحة والقياسي) توفر إشارة مرئية عن مقدار العمل الذي تم إنجازه، مع مراعاة العمل الذي تم فقط خلال \"الوقت الفعلي\" للعمل.\n" +
                "الأجزاء الخضراء تظهر مقدار العمل الذي تم إنجازه بالنسبة إلى الوقت المتوقع الكلي (سواء كان حصة قياسية أو حصة إزاحة). الجزء الأخضر الأكبر يعني أن العملية تتقدم وفقًا للمعدل المتوقع أو \"القياسي\"، بينما تشير الأجزاء الخضراء الأصغر أو المفقودة إلى التأخيرات أو عدم الكفاءة.",
            summaryExplanation: "الملخص:\n" +
                "الأجزاء الزرقاء: تعرض العمل الذي تم إنجازه خلال الفترة المخصصة.\n" +
                "الأجزاء الخضراء: تعرض مقدار العمل الذي تم إنجازه ضمن الحصة المحسوبة، مما يشير إلى الكفاءة والتوافق مع التوقعات.\n" +
                "من خلال متابعة هذه الأقسام الملونة، يوفر التقرير رؤى حول الوقت وكفاءة عملية التجميع لكل عقدة في سير العمل."


        }
    }
};
