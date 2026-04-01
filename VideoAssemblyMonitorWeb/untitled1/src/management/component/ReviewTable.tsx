//
// ReviewTable.tsx
//
import React, { useEffect, useMemo, useState } from "react";
import { Button, Table } from "antd";
import Column from "antd/es/table/Column";
import { StateMachineLog } from "../entity/StateMachineLog.ts";
import axios, { AxiosResponse } from "axios";
import { PresetNode } from "../entity/PresetNode.ts";
import TimelineModal from "./TimelineModal.tsx";
import { host } from "../../Share.tsx";
import { useLanguage } from "../../LanguageContext";

export class StateMachineLogStrings {
    id: number;
    user: string;
    preset: string;
    start_time: string;
    end_time: string;
    duration: number;

    constructor(data: StateMachineLog) {
        this.id = data.id;
        this.preset = data.preset.name;
        this.start_time = data.start_time.toString();
        this.end_time = data.start_time.toString();
        this.user = data.user;
        this.duration = data.duration;
    }
}

const ReviewTable: React.FC = () => {
    const { language } = useLanguage();

    const [loadingLog, setLoadingLog] = useState<StateMachineLogStrings | undefined>(undefined);
    const [timelineData, setTimelineData] = useState<
         AxiosResponse<Map<number, PresetNode>, unknown>
        | undefined
    >(undefined);
    const [showModal, setShowModal] = useState<boolean>(false);
    const [data, setData] = useState<StateMachineLogStrings[]>([]);

    function loadTimeline(logStrings: StateMachineLogStrings) {
        if (!logStrings) return;
        setLoadingLog(logStrings);
        Promise.all([
            axios.get(`${host}/review/state-machine-logs/${logStrings.id}/timeline`)
        ])
            .then(r => {
                setTimelineData(r[0]);
                setShowModal(true);
            })
            .catch(err => {
                console.error(err);
            });
    }

    useEffect(() => {
        // fetchLogs will refetch on an interval unless the modal is open
        const fetchLogs = () => {
            if (showModal) return;
            axios.get(`${host}/review/state-machine-logs`)
                .then((response: { data: StateMachineLog[] }) => {
                    setData(response.data.map(d => new StateMachineLogStrings(d)));
                })
                .catch((error: string) => console.error("Error fetching progress", error));
        };
        const intervalId = setInterval(fetchLogs, 2000);
        fetchLogs();
        // Clean up the interval on component unmount
        return () => clearInterval(intervalId);
    }, [showModal]);

    // Filters – remove duplicates using a Set
    const nameFilters = useMemo(() => {
        const uniqueUsers = Array.from(new Set(data.map(d => d.user)));
        return uniqueUsers.map(u => ({ text: u, value: u }));
    }, [data]);

    const presetFilters = useMemo(() => {
        const uniquePresets = Array.from(new Set(data.map(d => d.preset)));
        return uniquePresets.map(p => ({ text: p, value: p }));
    }, [data]);

    return (
        <>
            <Table<StateMachineLogStrings>
                pagination={false}
                style={{
                    width: "100%",
                    height: "100%",
                    backgroundColor: "#eee",
                    borderRadius: "16px",
                    margin: "0 auto",
                }}
                size="large"
                bordered
                dataSource={data}
                rowKey={(record) => record.id}
            >
                {/* ID column */}
                <Column<StateMachineLogStrings>
                    title={language.review.tableHeaders.id}
                    dataIndex="id"
                    key="id"
                    sorter={(a, b) => a.id - b.id}
                />

                {/* Operator column */}
                <Column<StateMachineLogStrings>
                    title={language.review.tableHeaders.operator}
                    dataIndex="user"
                    key="user"
                    filters={nameFilters}
                    onFilter={(value, record) => record.user === value}
                    sorter={(a, b) => a.user.localeCompare(b.user)}
                />

                {/* Preset column */}
                <Column<StateMachineLogStrings>
                    title={language.review.tableHeaders.preset}
                    dataIndex="preset"
                    key="preset"
                    filters={presetFilters}
                    onFilter={(value, record) => record.preset === value}
                    sorter={(a, b) => a.preset.localeCompare(b.preset)}
                />

                {/* Start Time */}
                <Column<StateMachineLogStrings>
                    title={language.review.tableHeaders.startTime}
                    dataIndex="start_time"
                    key="startTime"
                    sorter={(a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()}
                />

                {/* End Time */}
                <Column<StateMachineLogStrings>
                    title={language.review.tableHeaders.endTime}
                    dataIndex="end_time"
                    key="endTime"
                    sorter={(a, b) => new Date(a.end_time).getTime() - new Date(b.end_time).getTime()}
                />

                {/* Duration */}
                <Column<StateMachineLogStrings>
                    title={language.review.tableHeaders.duration}
                    dataIndex="duration"
                    key="duration"
                    sorter={(a, b) => a.duration - b.duration}
                />

                {/* Observations (View In Chart) */}
                <Column<StateMachineLogStrings>
                    title={language.review.tableHeaders.observations}
                    key="observations"
                    render={(_, record) => (
                        <Button
                            type="primary"
                            loading={loadingLog === record}
                            onClick={() => loadTimeline(record)}
                        >
                            {language.review.tableHeaders.viewInChart}
                        </Button>
                    )}
                />
            </Table>

            {/* Timeline Modal */}
            {timelineData && loadingLog && (
                <TimelineModal
                    isOpen={showModal}
                    timelineData={timelineData}
                    logName={`${language.review.timeline.logNoPrefix}${loadingLog.id}`}
                    setLoadingLog={setLoadingLog}
                    setShowModal={setShowModal}
                    setTimelineData={setTimelineData}
                    loadingLog={loadingLog}
                />
            )}
        </>
    );
};

export default ReviewTable;
