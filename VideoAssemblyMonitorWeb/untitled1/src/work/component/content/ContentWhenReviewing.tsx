import React, {
    Dispatch,
    SetStateAction,
    useCallback,
    useEffect,
    useRef,
    useState,
} from "react";
import axios from "axios";
import { ProgressBar } from "../../entity/Progress";
import { host } from "../../../Share";
import {
    RawSinglePredictionsMap,
    SinglePrediction,
    SinglePredictionsMap
} from "../../../management/entity/SinglePrediction";

interface Props {
    user: string;
    setProgressBars: Dispatch<SetStateAction<ProgressBar[]>>;
}

const ContentWhenReviewing: React.FC<Props> = ({ user, setProgressBars }) => {
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    const [videoUrl, setVideoUrl] = useState<string>("");
    const [intervalId, setIntervalId] = useState<number | null>(null);

    /**
     * 1) 加载视频文件流 -> 转为 objectURL
     */
    useEffect(() => {
        axios
            .get(`${host}/video/dl/${user}`, { responseType: "blob" })
            .then((res) => {
                const blob = res.data;
                const objectURL = URL.createObjectURL(blob);
                setVideoUrl(objectURL);
            })
            .catch((err) => {
                console.error("Failed to fetch video:", err);
                setVideoUrl("");
            });
    }, [user]);

    /**
     * 2) 绘制预测框（让 canvas 大小 = video 的“实际渲染尺寸” offsetWidth/Height）
     */
    const drawPredictions = useCallback((predictions: SinglePrediction[]) => {
        const videoEl = videoRef.current;
        const canvasEl = canvasRef.current;
        if (!videoEl || !canvasEl) return;

        // 视频在页面中实际渲染大小
        const actualWidth = videoEl.offsetWidth;
        const actualHeight = videoEl.offsetHeight;

        // 将 canvas 设置成相同像素大小
        canvasEl.width = actualWidth;
        canvasEl.height = actualHeight;

        const ctx = canvasEl.getContext("2d");
        if (!ctx) return;

        ctx.clearRect(0, 0, actualWidth, actualHeight);

        // 如果后端预测基于视频原分辨率 (video.videoWidth x video.videoHeight):
        const naturalWidth = videoEl.videoWidth;   // 原始宽度
        const naturalHeight = videoEl.videoHeight; // 原始高度

        // 计算缩放因子
        const scaleX = actualWidth / naturalWidth;
        const scaleY = actualHeight / naturalHeight;

        // 调试: 给 canvas 画个蓝色外边框
        // ctx.strokeStyle = "blue";
        // ctx.lineWidth = 4;
        // ctx.strokeRect(0, 0, actualWidth, actualHeight);

        // 画预测框
        predictions.forEach((p:SinglePrediction) => {
            const { x, y, width, height, confidence, clazz } = p;

            // 将原始分辨率坐标 -> 实际渲染坐标
            const drawX = x * scaleX;
            const drawY = y * scaleY;
            const drawW = width * scaleX;
            const drawH = height * scaleY;

            ctx.strokeStyle = "red";
            ctx.lineWidth = 2;
            ctx.strokeRect(drawX, drawY, drawW, drawH);

            const text = `${clazz} (${(confidence * 100).toFixed(1)}%)`;
            ctx.fillStyle = "red";
            ctx.font = "16px Arial";
            ctx.fillText(text, drawX, Math.max(0, drawY - 5));
        });
    }, []);

    /**
     * 请求进度条
     */
    const resetProgressBars = useCallback(
        (timestamp: number) => {
            axios
                .get(`${host}/progress?name=${user}&timestamp=${timestamp}`)
                .then((res: { data: ProgressBar[] }) => {
                    const bars = res.data.map(
                        (bar) =>
                            new ProgressBar(
                                bar.index,
                                bar.name,
                                bar.quota,
                                bar.parent,
                                bar.progress,
                                bar.p * 100
                            )
                    );
                    bars.sort((a) => a.index);
                    setProgressBars(bars);
                })
                .catch((err) => console.error("Error fetching progress", err));
        },
        [user, setProgressBars]
    );

    /**
     * 请求预测 -> draw
     */
    const fetchAndDrawPredictions = useCallback(
        (timestamp: number) => {
            axios
                .get(`${host}/predictions?name=${user}&timestamp=${timestamp}`)
                .then((res) => {
                    // 先把类型放宽到 any[]，然后在处理完“class -> clazz”转换后，赋予 SinglePredictionsMap 类型
                    const rawPredictionsMap = res.data as RawSinglePredictionsMap;

                    // 新建一个符合 SinglePredictionsMap 的对象，用来存放转换后的结果
                    const predictionsMap: SinglePredictionsMap = {};

                    // 遍历每个时间戳对应的预测数组
                    Object.entries(rawPredictionsMap).forEach(([time, predictionsArray]) => {
                        // 将每个预测对象的 "class" 字段重命名为 "clazz"
                        predictionsMap[Number(time)] = predictionsArray.map((pred) => {
                            const { class: clazz, ...rest } = pred;
                            return {
                                ...rest,
                                // 将原本的 class 属性值塞到 clazz 字段里
                                clazz,
                            };
                        });
                    });
                    
                    let first = true;
                    let lastPrediction: SinglePrediction[] | undefined;
                    for (const predictionsKey in predictionsMap) {
                        if (parseFloat(predictionsKey) / 1000 >= timestamp && !first) {
                            break;
                        }
                        first = false;
                        lastPrediction = predictionsMap[predictionsKey];
                    }
                    if (lastPrediction) {
                        drawPredictions(lastPrediction);
                    }
                })
                .catch((err) => console.error("Error fetching predictions", err));
        },
        [user, drawPredictions]
    );

    /**
     * 播放时，每隔0.5s 获取当前播放时间 -> 请求进度 & 预测
     */
    const handleVideoPlay = useCallback(() => {
        if (videoRef.current) {
            if (intervalId) {
                clearInterval(intervalId);
            }
            const id = window.setInterval(() => {
                if (videoRef.current) {
                    const currentTime = videoRef.current.currentTime;
                    resetProgressBars(currentTime);
                    fetchAndDrawPredictions(currentTime);
                }
            }, 500);
            setIntervalId(id);
        }
    }, [intervalId, resetProgressBars, fetchAndDrawPredictions]);

    const handleVideoPause = useCallback(() => {
        if (intervalId) {
            clearInterval(intervalId);
            setIntervalId(null);
        }
    }, [intervalId]);

    const handleVideoEnded = useCallback(() => {
        if (intervalId) {
            clearInterval(intervalId);
            setIntervalId(null);
        }
    }, [intervalId]);

    /**
     * 拖动进度条后立即请求
     */
    const handleSeeked = useCallback(() => {
        if (videoRef.current) {
            const currentTime = videoRef.current.currentTime;
            resetProgressBars(currentTime);
            fetchAndDrawPredictions(currentTime);
        }
    }, [resetProgressBars, fetchAndDrawPredictions]);

    /**
     * 3) 渲染: 父容器用 flex，让 (video+canvas) 整体在父容器中水平垂直居中
     *    内层 div: position: relative; <video> + <canvas absolute>
     */
    return (
        <div
            style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                width: "100%",
                height: "100%",
                overflow: "hidden",
            }}
        >
            <div style={{ position: "relative", display: "inline-block" }}>
                <video
                    ref={videoRef}
                    src={videoUrl}
                    controls
                    style={{
                        maxWidth: "100%",
                        height: "auto",
                        display: "block",
                        objectFit: "contain",
                    }}
                    autoPlay
                    onPlay={handleVideoPlay}
                    onPause={handleVideoPause}
                    onEnded={handleVideoEnded}
                    onSeeked={handleSeeked}
                />
                <canvas
                    ref={canvasRef}
                    style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        pointerEvents: "none",
                    }}
                />
            </div>
        </div>
    );
};

export default ContentWhenReviewing;
