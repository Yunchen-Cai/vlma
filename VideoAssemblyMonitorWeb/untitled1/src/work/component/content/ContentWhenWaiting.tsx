import React, { Dispatch, SetStateAction, useCallback, useEffect, useState } from "react";
import { Flex, Button, Divider, Select, Progress } from "antd";
import Dragger from "antd/es/upload/Dragger";
import { InboxOutlined } from "@ant-design/icons";
import axios from "axios";
import { ProgressBar } from "../../entity/Progress";   // 调整路径
import { host } from "../../../Share";                 // 调整路径

interface Props {
    user: string;
    isProcessing: boolean;
    setIsProcessing: Dispatch<SetStateAction<boolean>>;
    setState: Dispatch<SetStateAction<"Waiting" | "Capturing" | "Reviewing">>;
    setProgressBars: Dispatch<SetStateAction<ProgressBar[]>>;
    chosenPreset: string;
    setChosenPreset: Dispatch<SetStateAction<string>>;
}

// 简化一下上传图标及进度圈的小组件
function DragIcon(props: { percent: number; isProcessing: boolean }) {
    if (props.isProcessing) {
        return <Progress type="circle" percent={props.percent} />;
    }
    return <InboxOutlined />;
}

const ContentWhenWaiting: React.FC<Props> = ({
                                                 user,
                                                 isProcessing,
                                                 setIsProcessing,
                                                 setState,
                                                 chosenPreset,
                                                 setChosenPreset,
                                             }) => {
    // 上传流程的本地 state
    const [uploadState, setUploadState] = useState<
        "waitingUpload" | "uploading" | "uploadDone"
    >("waitingUpload");

    // 服务器端可选的预设
    const [preset, setPreset] = useState<string[]>([]);

    // 离线处理进度
    const [prog, setProg] = useState<number>(0);

    // --- 获取预设列表，每隔5秒刷新一次 ---
    useEffect(() => {
        if (isProcessing) return;

        const fetchPreset = () => {
            axios
                .get(`${host}/all-preset`)
                .then((response: { data: string[] }) => {
                    setPreset(response.data);
                })
                .catch((error: string) => console.error("Error fetching presets", error));
        };

        fetchPreset();
        const intervalId = setInterval(fetchPreset, 5000);

        return () => clearInterval(intervalId);
    }, [isProcessing]);

    // --- 检查离线视频处理进度 ---
    useEffect(() => {
        if (!isProcessing) return;

        const intervalId = setInterval(() => {
            axios
                .get(`${host}/video/progress/${user}`)
                .then((response: { data: number }) => {
                    const p = Math.floor(response.data * 100);
                    setProg(p);
                    // 如果达到 100% 则切换到回放阶段
                    if (p >= 100) {
                        setState("Reviewing");
                        setIsProcessing(false);
                    }
                })
                .catch((error: string) => console.error("Error fetching progress", error));
        }, 1000);

        return () => clearInterval(intervalId);
    }, [user, isProcessing]);

    // --- 离线处理按钮点击后调用 ---
    const startProc = useCallback(() => {
        setIsProcessing(true);
        axios
            .get(`${host}/video/proc/${user}?preset=${chosenPreset}`)
            .then((response) => {
                console.log("后台视频处理完成：", response.data);
            })
            .catch((error) => console.error(error));
    }, [user, chosenPreset]);

    // --- 通知后端「开始在线捕捉」的接口 ---
    const sendStartSign = useCallback(() => {
        const formData = new FormData();
        axios
            .post(`${host}/start?user=${user}&preset=${chosenPreset}`, formData)
            .then((response) => {
                console.log("State Machine Start", response.data);
            })
            .catch((error) => {
                console.error("Error starting capture", error);
            });
    }, [user, chosenPreset]);

    // --- 点击「开始捕捉」按钮 ---
    const onClickStartCapture = useCallback(() => {
        setState("Capturing");
        sendStartSign();
    }, [setState, sendStartSign]);

    // 上传区域按钮的文字和类型
    const getType = useCallback(() => {
        switch (uploadState) {
            case "waitingUpload":
                return undefined;
            case "uploadDone":
            case "uploading":
                return "primary";
        }
    }, [uploadState]);

    const getText = useCallback(() => {
        switch (uploadState) {
            case "waitingUpload":
                return "Please (re)upload your video";
            case "uploadDone":
                return isProcessing ? "Processing..." : "Start analyse";
            case "uploading":
                return "uploading";
        }
    }, [uploadState, isProcessing]);

    return (
        <Flex
            vertical={false}
            justify={"center"}
            align={"self-end"}
            style={{ height: "100%" }}
        >
            {/* 左侧：在线捕捉 */}
            <Flex
                vertical={true}
                align={"center"}
                justify={"center"}
                style={{
                    width: "50%",
                    height: "100%",
                    gap: "10px",
                }}
            >
                <Flex
                    vertical={true}
                    style={{
                        width: 400,
                        gap: "10px",
                        margin: "auto 0px",
                    }}
                    justify={"center"}
                >
                    <div
                        style={{
                            fontSize: 28,
                            height: "fit-content",
                            lineHeight: "30px",
                            textAlign: "left",
                            marginLeft: "4px",
                        }}
                    >
                        Preset
                    </div>
                    <Select
                        disabled={isProcessing}
                        size="large"
                        value={chosenPreset || undefined}
                        placeholder="Select a preset"
                        style={{
                            width: 400,
                            color: isProcessing ? "#fff" : "unset",
                        }}
                        defaultValue={preset?preset[0]: undefined}
                        dropdownStyle={{ color: "#000" }}
                        options={preset.map((p: string) => ({ value: p, label: p }))}
                        onChange={(value: string) => setChosenPreset(value)}
                    />
                </Flex>

                <Divider
                    variant="dashed"
                    style={{ width: "100%", borderColor: "#fff" }}
                />

                <Button
                    type="primary"
                    disabled={isProcessing || chosenPreset === ""}
                    onClick={onClickStartCapture}
                    style={{
                        padding: "50px 50px",
                        margin: "auto auto",
                        maxWidth: 400,
                        width: "auto",
                        maxHeight: 80,
                        color: isProcessing ? "#aaa" : "unset",
                    }}
                >
                    <Flex vertical={true} justify={"center"} align={"center"}>
                        <div style={{ fontSize: 28 }}>Start Video Capture</div>
                        <div style={{ fontSize: 20 }}>(online analyse)</div>
                    </Flex>
                </Button>
            </Flex>

            <Divider
                variant="dashed"
                style={{ height: "100%", borderColor: "#fff" }}
                type="vertical"
            />

            {/* 右侧：离线上传 */}
            <div
                style={{
                    alignItems: "center",
                    justifyItems: "center",
                    width: "50%",
                    height: "inherit",
                    gap: 50,
                    padding: "200px 100px",
                }}
            >
                <Dragger
                    disabled={isProcessing}
                    name="video"
                    multiple={false}
                    action={`${host}/video/uploadAndSave/${user}`} // 上传到后端的接口
                    onChange={(info) => {
                        const { status } = info.file;
                        if (status !== "uploading") {
                            console.log(info.file, info.fileList);
                            setUploadState("uploading");
                        }
                        if (status === "done") {
                            console.log(`${info.file.name} file uploaded successfully.`);
                            setUploadState("uploadDone");
                        } else if (status === "error") {
                            console.error(`${info.file.name} file upload failed.`);
                            setUploadState("waitingUpload");
                        }
                    }}
                    maxCount={1}
                    style={{
                        backgroundColor: "#aaa",
                    }}
                >
                    <p className="ant-upload-drag-icon">
            <span>
              <DragIcon percent={prog} isProcessing={isProcessing} />
            </span>
                    </p>
                    <p className="ant-upload-text" style={{ fontSize: 24 }}>
                        Upload video to offline analyse
                    </p>
                    <p className="ant-upload-hint" style={{ fontSize: 18 }}>
                        Click or drag file to this area to upload
                    </p>
                </Dragger>

                <Button
                    block
                    size={"large"}
                    disabled={uploadState === "waitingUpload" || chosenPreset === ""}
                    type={getType()}
                    loading={uploadState === "uploading" || isProcessing}
                    style={{
                        color: uploadState === "uploadDone" ? "#fff" : "#ccc",
                        fontSize: 20,
                    }}
                    onClick={startProc}
                >
                    {getText()}
                </Button>
            </div>
        </Flex>
    );
};

export default ContentWhenWaiting;
