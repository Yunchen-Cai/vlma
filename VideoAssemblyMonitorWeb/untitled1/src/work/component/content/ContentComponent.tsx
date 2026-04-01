import React, { Dispatch, SetStateAction, useState } from "react";
import { Content } from "antd/es/layout/layout";
import { ProgressBar } from "../../entity/Progress";  // 根据你自己代码中的实际路径调整
import { bgColorOfElement1 } from "../../../Share";    // 同理，调整路径
import ContentWhenWaiting from "./ContentWhenWaiting";
import ContentWhenCapturing from "./ContentWhenCapturing";
import ContentWhenReviewing from "./ContentWhenReviewing";

// 父组件接收的 Props，可以根据自己的实际情况适当增减
interface Props {
    setState: Dispatch<SetStateAction<"Waiting" | "Capturing" | "Reviewing">>;
    user: string;
    state: "Waiting" | "Capturing" | "Reviewing";
    isProcessing: boolean;
    setIsProcessing: Dispatch<SetStateAction<boolean>>;
    setProgressBars: Dispatch<SetStateAction<ProgressBar[]>>;
}

const contentStyle: React.CSSProperties = {
    margin: "0 8px",
    textAlign: "center",
    minHeight: 120,
    lineHeight: "120px",
    color: "#fff",
    backgroundColor: bgColorOfElement1,
    borderRadius: 15,
    overflow: "hidden",
};

const ContentComponent: React.FC<Props> = ({
                                               setState,
                                               user,
                                               state,
                                               isProcessing,
                                               setIsProcessing,
                                               setProgressBars,
                                           }) => {
    // 存放一些会被不同子组件用到的状态
    const [chosenPreset, setChosenPreset] = useState<string>("");

    if (state === "Waiting") {
        return (
            <Content style={contentStyle}>
                <ContentWhenWaiting
                    user={user}
                    isProcessing={isProcessing}
                    setIsProcessing={setIsProcessing}
                    setState={setState}
                    setProgressBars={setProgressBars}
                    chosenPreset={chosenPreset}
                    setChosenPreset={setChosenPreset}
                />
            </Content>
        );
    } else if (state === "Capturing") {
        return (
            <Content style={contentStyle}>
                <ContentWhenCapturing
                    user={user}
                    setState={setState}
                    setProgressBars={setProgressBars}
                    chosenPreset={chosenPreset}
                />
            </Content>
        );
    } else {
        return (
            <Content style={contentStyle}>
                <ContentWhenReviewing
                    user={user}
                    setProgressBars={setProgressBars}
                />
            </Content>
        );
    }
};

export default ContentComponent;
