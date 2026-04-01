//
// TimelineModal.tsx
//
import React, {Dispatch, SetStateAction, useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {Chart} from 'react-google-charts';
import {AxiosResponse} from "axios";
import {PresetNode} from "../entity/PresetNode.ts";
import {
    Button,
    Col,
    ConfigProvider,
    Modal,
    Progress,
    Radio,
    RadioChangeEvent,
    Row,
    Statistic,
    Switch,
    Tag,
    Tooltip
} from "antd";
import {StateMachineLogStrings} from "./ReviewTable.tsx";
import {useLanguage} from "../../LanguageContext";
import {useReactToPrint} from 'react-to-print';

interface TimelineEntry {
    node: PresetNode;
    rank: number;
    timestamp: Date;
    quota_of_rank: number;
}

interface TimelineModalProps {
    isOpen: boolean;
    timelineData: AxiosResponse<Map<number, PresetNode>, unknown>;
    logName: string;
    loadingLog: StateMachineLogStrings;
    setLoadingLog: Dispatch<StateMachineLogStrings | undefined>;
    setShowModal: Dispatch<SetStateAction<boolean>>;
    setTimelineData: Dispatch<SetStateAction<AxiosResponse<Map<number, PresetNode>, unknown> | undefined>>;
}

/**
 * 包含Timeline的Modal
 *
 *                         // 第一个圈圈：指示在理论上的该工序执行时间内，工序的执行情况，
 *                         //      蓝色为Quota所占时间，即蓝色越多，工序的理论执行时间内Handling时间越短。
 *                         //      绿色为实际工作所占时间。正常来说，绿色应该完全覆盖蓝色，指示在理论上该工序的执行时间内，实际工作时间约等于Quota时间。
 *                         //      若绿色很少，蓝色很多的话，说明实际工作时间基本不在理论上该工序的执行时间内，指示工序执行时间过低，或者执行时机错误。
 *                         // 第二个圈圈：指示该工序的实际上的执行时间段内，工序的执行情况，
 *                         //      蓝色为在偏置quota中实际工作的时间占所有实际执行时间段的比例（不含Handling），若没有满，说明在该时间段内，有其他工序被执行。
 *                         //
 */
const TimelineModal: React.FC<TimelineModalProps> = ({
                                                         isOpen,
                                                         timelineData,
                                                         logName,
                                                         loadingLog,
                                                         setTimelineData,
                                                         setShowModal,
                                                         setLoadingLog
                                                     }) => {
    const { language } = useLanguage();

    // raw vs filtered
    const [mode, setMode] = useState<'raw' | 'report'>('raw');
    const [timelineEntry, setTimelineEntry] = useState<TimelineEntry[]>();
    const [realTime, setRealTime] = useState<Map<PresetNode, number>>();
    const [timeAnalysis, setTimeAnalysis] = useState<number[][]>();
    const [displayHandling, setDisplayHandling] = useState<boolean>(true);
    const reportRef = useRef<HTMLDivElement>(null);

    const handleCloseModal = useCallback(() => {
        setLoadingLog(undefined);
        setShowModal(false);
        setTimelineData(undefined);
    }, [setLoadingLog, setShowModal, setTimelineData]);

    const getHigherKey = useCallback((key: number) => {
        if (!timelineEntry) return new Date(key);
        const futureKeys = timelineEntry
            .filter(entry => entry.timestamp.getTime() > key)
            .map(e => e.timestamp.getTime());
        if (futureKeys.length === 0) {
            // fallback to log end: start time + duration
            return new Date(new Date(loadingLog.start_time).getTime() + loadingLog.duration);
        }
        return new Date(Math.min(...futureKeys));
    }, [timelineEntry, loadingLog]);

    const getNextKeyWithoutHandling = useCallback((key: Date) => {
        if (timelineEntry === undefined) return new Date(key);
        while (timelineEntry.find(e=>(e.timestamp.getTime() <= key.getTime())&&(getHigherKey(e.timestamp.getTime()).getTime() > key.getTime()))?.node.rank === -1)
            key = getHigherKey(key.getTime());
        return key;
    }, [getHigherKey, timelineEntry]);

    const getHighestKeyOfLessRank = useCallback((defaultKey: number, rank: number) => {
        if (!timelineEntry) return new Date(defaultKey);
        if (rank === 1) return new Date(defaultKey);
        const keys = timelineEntry
            .filter(e => e.rank === rank - 1)
            .map(e => e.timestamp.getTime());
        if (keys.length === 0) return new Date(defaultKey);
        const maxParent = Math.max(...keys);
        const higherKey = getHigherKey(maxParent);
        return getNextKeyWithoutHandling(higherKey);
    }, [timelineEntry, getHigherKey]);

    // Prepare chart data for google-charts Timeline
    const chartData = useMemo(() => {
        const columns = [
            { type: 'string', id: 'Position' },
            { type: 'string', id: 'Name' },
            { type: 'date', id: 'Start' },
            { type: 'date', id: 'End' }
        ];
        if (!timelineEntry) return columns;

        // Rows for offset-quota segment, real-work segment, standard-quota segment...
        const rows: (string | Date)[][] = [];
        const usedNodes: number[] = [];

        const copyTimeline = [...timelineEntry];
        copyTimeline.sort((a, b) => a.rank - b.rank);

        // 1) offset quota block
        copyTimeline.forEach(entry => {
            if ((!usedNodes.includes(entry.node.id.number)) && entry.rank !== -1) {
                usedNodes.push(entry.node.id.number);
                const category = `${entry.node.id.number}. ${entry.node.name}`;
                const stateLabel = language.review.timeline.offsetQuota;
                const start = getHighestKeyOfLessRank(entry.timestamp.getTime(), entry.rank);
                // const start = entry.timestamp;
                const end = new Date(start.getTime() + entry.quota_of_rank * 1000);
                // Make sure start < end for chart
                const rowStart = (start.getTime() < end.getTime()) ? start : end;
                const rowEnd = (start.getTime() < end.getTime()) ? end : start;
                rows.push([category, stateLabel, rowStart, rowEnd]);
            }
        });

        // 2) real work block
        copyTimeline.forEach(entry => {
            const category = `${entry.node.id.number}. ${entry.node.name}`;
            const stateLabel = language.review.timeline.realWork;
            const start = entry.timestamp;
            const end = getHigherKey(entry.timestamp.getTime());
            const rowStart = (start.getTime() < end.getTime()) ? start : end;
            const rowEnd = (start.getTime() < end.getTime()) ? end : start;
            rows.push([category, stateLabel, rowStart, rowEnd]);
        });

        // 3) standard quota block
        let t = new Date(Math.min(...copyTimeline.map(e => e.timestamp.getTime())));
        const usedStdQuota: number[] = [];
        copyTimeline.forEach(entry => {
            if ((!usedStdQuota.includes(entry.node.id.number)) && entry.rank !== -1) {
                usedStdQuota.push(entry.node.id.number);
                const category = `${entry.node.id.number}. ${entry.node.name}`;
                const stateLabel = language.review.timeline.standardQuota;
                const start = getNextKeyWithoutHandling(new Date(t));
                const end = new Date(start.getTime() + entry.node.calculating_quota * 1000);
                // Update t
                if (entry.rank !== -1) t = end;
                // Make sure start < end
                const rowStart = (start.getTime() < end.getTime()) ? start : end;
                const rowEnd = (start.getTime() < end.getTime()) ? end : start;
                rows.push([category, stateLabel, rowStart, rowEnd]);
            }
        });

        // Return combined array
        return [columns, ...rows];
    }, [timelineEntry, language, getHighestKeyOfLessRank, getHigherKey]);

    useEffect(() => {
        const rawData = timelineData;
        // 这里可能需要从后端返回的数据结构做一些转换，这里假设返回结构还是 (Map<number, PresetNode>) 的形式
        // 注意 AxiosResponse.data 若是对象，也可能需要手动转换为 Map
        const dataMap = new Map(Object.entries(rawData.data));
        console.log(dataMap);
        // 统计 rank -> total_quota
        const quotaOfRankMap = new Map<number, number>();
        const quotaAlreadyShown: number[] = [];

        dataMap.forEach((v: PresetNode) => {
            if (!quotaAlreadyShown.includes(v.id.number)) {
                quotaAlreadyShown.push(v.id.number);
                const oldVal = quotaOfRankMap.get(v.rank) || 0;
                quotaOfRankMap.set(v.rank, oldVal + v.calculating_quota);
            }
        });

        const t: TimelineEntry[] = [];
        dataMap.forEach((v: PresetNode, k) => {
            const q = quotaOfRankMap.get(v.rank) || 0;
            let timestampNum = parseInt(k);
            // 如果时间戳可能是相对值 < 100000，就用 start_time 进行偏移
            if (timestampNum < 100000) {
                timestampNum += new Date(loadingLog.start_time).getTime();
            }
            t.push({
                node: v,
                rank: v.rank,
                timestamp: new Date(timestampNum),
                quota_of_rank: q
            });
        });
        setTimelineEntry(t);
        // “raw” 模式：使用 rawData
        // “report” 模式：我们的 timelineEntry 不再使用 filteredData 画图，但你也可以根据需要决定要不要设置 timelineEntry
        //   如果“report”模式不需要画图，可以只在“raw”中生成 timelineEntry
        if (mode === "raw") {
            if (!displayHandling) {
                let timePointerWithoutHandling = 0;
                let handlingTime = 0;

                const updatedEntries: TimelineEntry[] = [];
                t.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

                t.forEach((entry) => {

                    const time = getHigherKey(entry.timestamp.getTime()).getTime();
                    // console.log("time", time);
                    // console.log("entry.timestamp.getTime()", entry.timestamp.getTime());
                    let duration = (time - entry.timestamp.getTime());
                    if (duration >= 1000000) duration -= new Date(loadingLog.start_time).getTime()

                    if (entry.node.rank === -1) {
                        // 如果是 Handling 节点 (rank = -1)
                        handlingTime += duration;
                    } else {
                        // 如果不是 Handling 节点
                        entry.timestamp = new Date(timePointerWithoutHandling + new Date(loadingLog.start_time).getTime()); // 更新时间戳
                        timePointerWithoutHandling += duration; // 根据 real_quota 更新时间指针
                        // 将更新后的 entry 添加到结果数组
                        updatedEntries.push(entry);
                    }
                });
                const handling= t.find(o => o.rank == -1);

                if (handling != undefined) {
                    handling.timestamp = new Date(loadingLog.duration - handlingTime + new Date(loadingLog.start_time).getTime());
                    updatedEntries.push(handling)
                }
                setTimelineEntry(updatedEntries);
            }
        } else {
            // 创建一个新的 Map 来合并具有相同 id.number 的 PresetNode
            // 遍历 rawData 进行合并
            const dataMap = new Map<number, PresetNode>();

            const ids = new Map<number, PresetNode>();
            new Map(Object.entries(rawData.data)).forEach((node,key, ) => {
                // 使用 node.id.number 作为唯一标识符
                const nodeId = node.id.number;

                // 检查该 id 是否已经存在于 dataMap 中
                if (ids.has(nodeId)) {
                    // 如果存在，合并数据
                    const value = ids.get(nodeId);
                    console.assert(value instanceof PresetNode);
                    if (value === undefined) return;
                    dataMap.set(parseInt(key), value);
                } else {
                    // 如果该 id 不存在，直接加入 dataMap
                    ids.set(nodeId, node);
                    dataMap.set(parseInt(key), node);
                }
            });
            const realTimeMap = new Map<PresetNode, number>(); // Key is PresetNode

            // Calculate the actual usage time for each node
            dataMap.forEach((node: PresetNode, startTime) => {
                const endTime = getHigherKey(startTime).getTime();
                const usageTime = endTime - startTime;  // Calculate the actual usage time

                // Store the real-time usage for each node (using PresetNode as key)
                let newVar = realTimeMap.get(node);
                if (newVar === undefined){
                    newVar = 0;
                }
                newVar += usageTime;
                realTimeMap.set(node, newVar);  // Use PresetNode as the key
            });
            // Set the real-time data map
            setRealTime(realTimeMap);
            const getIntersection = (a: (string | Date)[][], b: (string | Date)[][]): (string | Date)[][] => {
                const result: (string | Date)[][] = [];

                // 遍历 a 和 b 中的每一对区间
                for (let i = 0; i < a.length; i ++) {
                    const startA = a[i][2] instanceof Date ? a[i][2] : new Date(a[i][2]);
                    const endA = a[i][3] instanceof Date ? a[i][3] : new Date(a[i][3]);

                    for (let j = 0; j < b.length; j ++) {
                        const startB = b[j][2] instanceof Date ? b[j][2] : new Date(b[j][2]);
                        const endB = b[j][3] instanceof Date ? b[j][3] : new Date(b[j][3]);

                        if (!(startA instanceof Date
                            && startB instanceof Date
                            && endA instanceof Date
                            && endB instanceof Date)) return [];

                        // 计算交集的开始和结束时间
                        const intersectionStart = new Date(Math.max(startA.getTime(), startB.getTime()));
                        const intersectionEnd = new Date(Math.min(endA.getTime(), endB.getTime()));

                        // 如果交集有效，即开始时间小于结束时间
                        if (intersectionStart < intersectionEnd) {
                            result.push([a[i][0] + ' ' + b[j][0],
                                a[i][1] + ' ' + b[j][1],
                                intersectionStart,
                                intersectionEnd]);
                        }
                    }
                }

                return result;
            };

            const getDuration = (a: (string | Date)[][]) => {
                let result: number = 0;
                for (let i = 0; i < a.length; i ++) {
                    const startA = a[i][2] instanceof Date ? a[i][2] : new Date(a[i][2]);
                    const endA = a[i][3] instanceof Date ? a[i][3] : new Date(a[i][3]);
                    if (!(startA instanceof Date
                        && endA instanceof Date)) continue;
                    result += endA.getTime() - startA.getTime();
                }
                return result;
            }

            const filtered_data = [...chartData].filter(o=>Array.isArray(o) && o.every(item => typeof item === 'string' || item instanceof Date))
            const highestNodeId = Math.max(...t.map((entry) => entry.node.id.number));
            const ranks: number[] = [];
            const result: number[][] = [];

            t.forEach(node => ranks[node.node.id.number] = node.rank);
            const handling = [...filtered_data].filter(o=> typeof o[0] === 'string' && o[0] == "0. Handling");
            for (let i = 1; i <= highestNodeId; i++) {
                const dataOfNode = [...filtered_data].filter(o=>typeof o[0] === 'string' && o[0].startsWith(i.toString()));
                const standardQuotaOfNode = dataOfNode.filter(data => data[1] == language.review.timeline.standardQuota)[0];
                const offsetQuotaOfNode = dataOfNode.filter(data => data[1] == language.review.timeline.offsetQuota)[0];
                const realWorkListOfNode: (string | Date)[][] = dataOfNode.filter(data => data[1] == language.review.timeline.realWork);

                offsetQuotaOfNode[2] = offsetQuotaOfNode[2] instanceof Date ? offsetQuotaOfNode[2] : new Date(loadingLog.start_time);
                standardQuotaOfNode[2] = standardQuotaOfNode[2] instanceof Date ? standardQuotaOfNode[2] : new Date(loadingLog.start_time);
                offsetQuotaOfNode[3] = offsetQuotaOfNode[3] instanceof Date ? offsetQuotaOfNode[3] : new Date(loadingLog.start_time + loadingLog.duration);
                standardQuotaOfNode[3] = standardQuotaOfNode[3] instanceof Date ? standardQuotaOfNode[3] : new Date(loadingLog.start_time + loadingLog.duration);

                const highestKeyOfLastRank = i==1?getNextKeyWithoutHandling(new Date(loadingLog.start_time)):getNextKeyWithoutHandling(getHighestKeyOfLessRank(offsetQuotaOfNode[2].getTime(), ranks[i]));
                const endOfThisRank = i == highestNodeId ? offsetQuotaOfNode[3] : getNextKeyWithoutHandling(getHighestKeyOfLessRank(offsetQuotaOfNode[3].getTime(), ranks[i]+1));

                const wholeTimeFromStandardStart = [`${i}. wholeTimeFromStandardStart`, "wholeTimeFromStandardStart", standardQuotaOfNode[2], endOfThisRank];
                const wholeTimeFromOffsetStart = [`${i}. wholeTimeFromOffsetStart`, "wholeTimeFromOffsetStart", highestKeyOfLastRank, endOfThisRank];

                const handlingsInStandardPeriod = getIntersection([wholeTimeFromStandardStart], handling);
                const handlingsInOffsetPeriod = getIntersection([wholeTimeFromOffsetStart], handling);

                const handlingsInStandardDuration = getDuration(handlingsInStandardPeriod);
                const handlingsInOffsetDuration = getDuration(handlingsInOffsetPeriod);

                standardQuotaOfNode[3] = new Date(standardQuotaOfNode[3].getTime() + handlingsInStandardDuration);
                offsetQuotaOfNode[3] = new Date(offsetQuotaOfNode[3].getTime() + handlingsInOffsetDuration);

                const realWorkInStandardPeriod = getIntersection([wholeTimeFromStandardStart], realWorkListOfNode);
                const realWorkInOffsetPeriod = getIntersection([offsetQuotaOfNode], realWorkListOfNode);

                const realWorkInStandardDuration = getDuration(realWorkInStandardPeriod);
                const realWorkInOffsetDuration =  getDuration(realWorkInOffsetPeriod);

                const standardQuotaWithHandling = standardQuotaOfNode[3].getTime() - standardQuotaOfNode[2].getTime();
                const offsetQuotaWithHandling = offsetQuotaOfNode[3].getTime() - offsetQuotaOfNode[2].getTime();

                result.push([
                    realWorkInStandardDuration,
                    realWorkInOffsetDuration,
                    standardQuotaWithHandling,
                    offsetQuotaWithHandling,
                    endOfThisRank.getTime() - standardQuotaOfNode[2].getTime(),
                    endOfThisRank.getTime() - highestKeyOfLastRank.getTime(),
                    getDuration(realWorkListOfNode)
                ])
            }
            setTimeAnalysis(result);
        }
    }, [mode, timelineData, loadingLog.start_time, displayHandling]);

    const handlePrint = useReactToPrint({
        contentRef: reportRef,
        pageStyle: `
            @page {
              size: A4 landscape;
              margin: 15mm;
            }
            html, body {
              font-family: Arial, sans-serif;
              background-color: white !important; /* Force white background */
              margin: 0;
              padding: 0;
            }
            rep {
              background-color: white !important; /* Ensure white background for report elements */
            }
            h2 {
              color: black !important; /* Force black color for h2 text */
            }
            h3 {
              color: black !important; /* Force black color for h2 text */
            }
            p {
              color: black !important; /* Force black color for h2 text */
            }
        }
        `,
    });
    // 导出 PDF 的回调：使用 jsPDF 将 reportRef 内的内容导出为 A4 大小 PDF
    const handleExportPDF = useCallback(() => {
        if (!reportRef.current) return;
        handlePrint();
    }, [reportRef]);

    const RenderReport = React.forwardRef(() => {
        if (!realTime) return null;

        // ============= 1) 计算各节点的 “时间重心” =============
        // key: node.id.number, value: 累积(时间片长度 * 时间片中点)，以及总时长
        const centerOfMassMap = new Map<number, number>(); // 累加 (mid * length)
        const lengthSumMap = new Map<number, number>();    // 累加 length

        // 遍历所有时间片
        if (timelineEntry == undefined) return null;
        timelineEntry.forEach(e => {
            // 跳过 Handling 节点（如果不需纳入排序）
            if (e.rank === -1) return;

            const nodeId = e.node.id.number;
            const start = e.timestamp.getTime();
            const end = getHigherKey(start).getTime();
            const length = end - start;
            const mid = start + length / 2;

            const oldWeighted = centerOfMassMap.get(nodeId) || 0;
            centerOfMassMap.set(nodeId, oldWeighted + mid * length);

            const oldLen = lengthSumMap.get(nodeId) || 0;
            lengthSumMap.set(nodeId, oldLen + length);
        });
        // 计算实际的中心 = (∑(mid*length)) / (∑length)
        centerOfMassMap.forEach((weightedSum, nodeId) => {
            const totalLength = lengthSumMap.get(nodeId) || 1;
            centerOfMassMap.set(nodeId, weightedSum / totalLength);
        });

        // ============= 2) 根据时间重心对所有节点排序 =============
        // 我们使用 realTime 的 keys 来遍历节点，也可以用 timelineEntry 中 node 去重后遍历
        // 拿到 rank != -1 的 PresetNode
        const normalNodes: PresetNode[] = Array.from(realTime.keys())
            .filter(n => n.rank !== -1);

        // 为了在后续渲染中，还需要 usageTime、中心值、甚至 node 自身 => 组装成一个数组
        interface NodeWithInfo {
            node: PresetNode;
            usageTime: number;
            center: number; // 时间重心
        }
        const nodeArray: NodeWithInfo[] = normalNodes.map(n => ({
            node: n,
            usageTime: realTime.get(n) || 0,
            center: centerOfMassMap.get(n.id.number) ?? 0
        }));

        // 排序
        nodeArray.sort((a, b) => a.center - b.center);

        // 给每个节点打上“执行顺序”的序号 index
        const nodeToIndex = new Map<number, number>();
        nodeArray.forEach((item, idx) => nodeToIndex.set(item.node.id.number, idx));

        // ============= 3) 校验节点与其父节点的顺序是否符合 DAG 前序要求 =============
        function checkPartialOrder(node: PresetNode): boolean {
            if (!node.parents || node.parents.length === 0) return true; // 无父节点，必然满足
            const selfIndex = nodeToIndex.get(node.id.number) ?? 999999;
            return node.parents.every(parent => {
                // Handling 与 rank=-1 的父节点就直接忽略，也可看需求处理
                if (parent.rank === -1) return true;
                const parentIndex = nodeToIndex.get(parent.id.number);
                if (parentIndex === undefined) {
                    // 可能 parent 还没纳入 nodeArray, 视情况而定
                    return true;
                }
                return parentIndex < selfIndex;
            });
        }

        return (
            <div className="rep"><ConfigProvider>
                {nodeArray.map((info, idx) => {
                    const node = info.node;
                    const usageTime = info.usageTime;
                    const partialOk = checkPartialOrder(node);

                    if (node.rank !== -1 && (timeAnalysis == undefined || timeAnalysis[node.id.number-1] == undefined)) {
                            return (
                                <div key={node.id.number} className="report-report">
                                    {language.review.timeline.procNotFound}
                                </div>
                            );
                        }
                        const quota = node.calculating_quota * 1000;
                        const overtime = usageTime > quota;
                        const overtimeRatio = overtime ? Math.min(1, (usageTime - quota) / quota) : 0;
                        const progressPercent = Math.min(100, (usageTime / quota) * 100);

                        const notDone = usageTime < (node.lower_quota * 1000);
                        const doneRatio = usageTime / (node.calculating_quota * 1000);
                        const ratioToDone = (node.lower_quota) / (node.calculating_quota);

                        const timeout = usageTime > (node.upper_quota * 1000);
                        const ratioToTimeout = (node.upper_quota) / (node.calculating_quota) - 1;
                        let green1 = 0;
                        let green2 = 0;
                        let blue1 = 0;
                        let blue2 = 0;
                        if (node.rank !== -1 && timeAnalysis != undefined) {

                            blue1 = timeAnalysis[node.id.number - 1][2] / timeAnalysis[node.id.number - 1][4]
                            green1 = timeAnalysis[node.id.number - 1][0] / timeAnalysis[node.id.number - 1][4] / Math.min(1, blue1)

                            blue2 = timeAnalysis[node.id.number - 1][1] / timeAnalysis[node.id.number - 1][3]
                            green2 = Math.min(1, (timeAnalysis[node.id.number - 1][3] / timeAnalysis[node.id.number - 1][5])) * Math.min(1, blue2)
                        }


                        return (
                            <div key={node.id.number} style={{ marginBottom: 16, }}>
                                <Row>
                                    <Col span={12}>
                                        <h2>{node.name} (ID: {node.id.number})</h2>
                                        <div style={{ marginTop: 8 }}>
                                            <Tag color={partialOk ? "green" : "red"}>
                                                {partialOk
                                                    ? language.review.timeline.orderIsAcceptable
                                                    : language.review.timeline.orderIsNotAcceptable}
                                            </Tag>
                                            <span style={{ marginLeft: 8 }}>
                                                {`${language.review.timeline.executionOrderLabel}${idx + 1}`}
                                            </span>
                                        </div>
                                    </Col>
                                    <Col span={12} style={{ textAlign: 'right' }}>

                                        <div style={{
                                            display: 'flex',
                                            justifyContent: 'right',
                                            gap: '30px',
                                            alignItems: 'center',
                                            marginBottom: '30px',
                                            marginTop: '30px',

                                        }}>
                                            {node.rank !== -1 && timeAnalysis != undefined &&
                                                <Tooltip title={`${language.review.timeline.realWorkInStandardDuration}: ${timeAnalysis[node.id.number - 1][0]}
                                                , ${language.review.timeline.standardQuotaWithHandling}: ${timeAnalysis[node.id.number - 1][2]}
                                                , ${language.review.timeline.wholeTimeFromStandardStart}: ${timeAnalysis[node.id.number - 1][4]}`}>
                                                    <Progress type="circle" percent={Math.floor(blue1* 100)}
                                                              success={{percent: Math.floor(green1* 100)}}
                                                              format={() => 'Standard'}
                                                    />
                                                </Tooltip>}
                                            {node.rank !== -1 && timeAnalysis != undefined &&
                                                <Tooltip title={`${language.review.timeline.realWorkInOffsetDuration}: ${timeAnalysis[node.id.number - 1][1]}
                                                , ${language.review.timeline.offsetQuotaWithHandling}: ${timeAnalysis[node.id.number - 1][3]}
                                                , ${language.review.timeline.wholeTimeFromOffsetStart}: ${timeAnalysis[node.id.number - 1][5]},
                                                ${language.review.timeline.realWorkTime}: ${timeAnalysis[node.id.number - 1][6]}`}>
                                                    <Progress type="circle" percent={Math.floor(blue2* 100)}
                                                              success={{percent: Math.floor(green2* 100)}}
                                                              format={() => 'Offset'}
                                                    />
                                                </Tooltip>}
                                            <Statistic
                                                title={language.review.timeline.realWorkTime}
                                                value={(usageTime / 1000).toFixed(1)}
                                                suffix={language.common.s}
                                            />
                                            <Statistic
                                                title={language.review.timeline.modelStandardTime}
                                                value={node.calculating_quota.toFixed(1)}
                                                suffix={language.common.s}
                                            />
                                            {node.name !== "Handling" && <Statistic
                                                title={language.review.timeline.modelStandardBounds}
                                                value={node.lower_quota.toFixed(1) + "-" + node.upper_quota.toFixed(1)}
                                                suffix={language.common.s}
                                            />}
                                        </div>
                                    </Col>
                                </Row>
                                <Row>
                                    <Col span={24}>
                                        <Progress
                                            type="line"
                                            percent={notDone ?ratioToDone*100:progressPercent}
                                            format={() => `${Math.floor(progressPercent)}%`}
                                            size={['100%', 20]}
                                            strokeColor={ notDone ?
                                                {
                                                    '0%': '#52c41a',
                                                    [doneRatio*100]: '#52c41a',
                                                    [doneRatio*100+0.01]: '#fa5c5c',
                                                    [ratioToDone*100]: '#fa5c5c',
                                                    '100%': '#ffffff',
                                                }:{
                                                    '0%': '#52c41a',
                                                    '100%': '#52c41a',
                                                }
                                            }
                                            status={(!notDone) || node.name == "Handling" ? "normal" : "exception"}
                                        />
                                    </Col>
                                </Row>
                                {overtime && (
                                    <Row style={{ marginTop: 8 }}>
                                        <Col span={24}>
                                            <Progress
                                                type="line"
                                                percent={timeout ? overtimeRatio * 100 : ratioToTimeout * 100}
                                                format={() => `${language.review.timeline.totalTimeout} ${Math.floor(((usageTime - quota) / quota) * 100)}%`}
                                                size={['100%', 20]}
                                                strokeColor={ timeout ?
                                                    {
                                                        '0%': '#52c41a',
                                                        [ratioToTimeout*100]: '#52c41a',
                                                        [ratioToTimeout*100+0.01]: "#fa5c5c",
                                                        [overtimeRatio*100]: "#fa5c5c",
                                                        '100%': '#ffffff',
                                                    }:{
                                                        '0%': '#52c41a',
                                                        [overtimeRatio*100]: '#52c41a',
                                                        [overtimeRatio*100+0.01]: "#faad14",
                                                        [ratioToTimeout*100]: "#faad14",
                                                        '100%': '#ffffff',
                                                    }
                                                }
                                                status={timeout ? "exception" : "normal"}
                                            />
                                        </Col>
                                    </Row>
                                )}
                            </div>
                        );
                    }
                )}
                <div style={{ marginTop: 32, padding: 20, borderTop: '1px solid #ddd' }}>
                    <h3>{language.review.timeline.progressExplanationTitle}</h3>
                    <p>{language.review.timeline.offsetProgressExplanation}</p>
                    <p>{language.review.timeline.standardProgressExplanation}</p>
                    <p>{language.review.timeline.blueGreenExplanation}</p>
                    <p>{language.review.timeline.summaryExplanation}</p>
                </div>
            </ConfigProvider>
            </div>
        );
    });

    return (
        <Modal
            open={isOpen}
            onOk={handleCloseModal}
            onCancel={handleCloseModal}
            width="90%"
            title={`${language.review.timeline.titlePrefix}${logName}`}
        >
            <div style={{ marginBottom: 16 }}>
                <Radio.Group
                    optionType="button"
                    buttonStyle="solid"
                    onChange={(e: RadioChangeEvent) => {
                        if(e.target.value == "report"){
                            setDisplayHandling(true);
                        }
                        setMode(e.target.value)
                    }}
                    value={mode}
                    disabled={!displayHandling}
                >
                    <Radio.Button value="raw">
                        {language.review.timeline.rawData}
                    </Radio.Button>
                    <Radio.Button value="report">
                        {language.review.timeline.reportTitle}
                    </Radio.Button>
                </Radio.Group>
                {mode === 'report' && (
                    <Tooltip title={language.review.timeline.exportBackgroundGraphMessage}>
                        <Button
                            type="primary"
                            style={{ marginLeft: 40 }}
                            onClick={handleExportPDF}
                        >{language.review.timeline.exportToPDF}</Button>
                    </Tooltip>
                )}
            </div>

            {
                mode === 'raw' && (
                    <div>
                    <Switch
                        defaultChecked={true}
                        onChange={setDisplayHandling}
                        checkedChildren="Display Handling"
                        unCheckedChildren="Filter Handling"
                        style={ {
                            marginBottom: "20px"
                        }}
                    >

                    </Switch>
                    <Chart
                        chartType="Timeline"
                        data={chartData}
                        width="100%"
                        height="70vh"
                        loader={<div>{language.common.loadingChart}</div>}
                        options={{
                            timeline: { showBarLabels: true }
                        }}
                    /></div>
                )
            }
            <div ref={reportRef} className="rep">
                {mode === 'report' && <RenderReport/>}
            </div>
        </Modal>
    );
};

export default TimelineModal;




