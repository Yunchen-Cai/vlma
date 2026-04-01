import React, {
    Dispatch,
    SetStateAction,
    useCallback,
    useEffect,
    useRef,
} from "react";
import Webcam from "react-webcam";
import axios from "axios";
import { ProgressBar } from "../../entity/Progress";  // 调整路径
import { host } from "../../../Share";                // 调整路径

interface Props {
    user: string;
    setState: Dispatch<SetStateAction<"Waiting" | "Capturing" | "Reviewing">>;
    setProgressBars: Dispatch<SetStateAction<ProgressBar[]>>;
    chosenPreset: string;
}

const ContentWhenCapturing: React.FC<Props> = ({
                                                   user,
                                                   setProgressBars,
                                               }) => {
    const webcamRef = useRef<Webcam | null>(null);
    const intervalRef = useRef<number | null>(null);

    // 每隔1秒截屏一次，上传给后端
    const capture = useCallback(() => {
        if (!webcamRef.current) return;
        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) return;

        // 将截图以 Base64 / Blob 形式发送给后端
        const formData = new FormData();
        formData.append("img", imageSrc);
        formData.append("user", user);
        formData.append("t", Date.now().toString());

        axios
            .post(`${host}/video/img`, formData)
            .then((response) => console.log(response.data))
            .catch((error) => console.error(error));

        // 同时获取后端进度条信息
        axios
            .get(`${host}/progress?name=${user}&timestamp=-1`)
            .then((response: { data: ProgressBar[] }) => {
                const l: ProgressBar[] = response.data.map((bar: ProgressBar) => {
                    return new ProgressBar(
                        bar.index,
                        bar.name == "Idle"? "Handling": bar.name,
                        bar.quota,
                        bar.parent,
                        bar.progress,
                        bar.p * 100
                    );
                });
                l.sort((a) => a.index);
                setProgressBars(l);
            })
            .catch((error) => console.error("Error fetching progress", error));
    }, [webcamRef, user, setProgressBars]);

    // 组件挂载后，启动定时器；组件卸载时，清除定时器
    useEffect(() => {
        intervalRef.current = window.setInterval(() => {
            capture();
        }, 1000);

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [capture]);

    return (
        <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            width="100%"
            height="100%"
            videoConstraints={{
                facingMode: "user",
            }}
        />
    );
};

export default ContentWhenCapturing;
