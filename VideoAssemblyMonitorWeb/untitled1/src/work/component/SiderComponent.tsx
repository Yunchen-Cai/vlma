import React, {useEffect, useRef} from 'react';
import {Flex} from 'antd';
import Sider from "antd/es/layout/Sider";
import {ProgressBar} from "../entity/Progress.tsx";
import {bgColorOfElement1} from "../../Share.tsx";

interface SiderProps {
    progressBars: ProgressBar[];
}

const siderStyle: React.CSSProperties = {
    marginRight: '8px',
    textAlign: 'center',
    lineHeight: '120px',
    color: '#fff',
    backgroundColor: bgColorOfElement1,
    borderRadius: 15,
    padding: '8px',
};


const SiderComponent: React.FC<SiderProps> = ({ progressBars }) => {


    const isIthProgressDone = React.useCallback((i: number) => {
        if (progressBars[i] != undefined) {
            const progressBars1 = progressBars.filter((p) => p.index == i);
            if (progressBars1.length > 0)  {
                const progressBar = progressBars1[0];
                if (progressBar != undefined)
                    return progressBar.progress > 0.80
                else return false
            }
            else return false
        }
        else return false;
    }, [progressBars]);

    // 为滚动容器创建 ref
    const containerRef = useRef<HTMLDivElement>(null);
    // 为每个进度条创建一个 ref 数组
    const progressRefs = useRef<Array<HTMLDivElement | null>>([]);

    // 每当 progressBars 变化时，查找未完成的进度条并判断其是否在可视区域内，如不在则自动滚动到该进度条
    useEffect(() => {
        let activeIndex: string|number = '-1';
        let maxP = -1;
        for (const progressBarsKey in progressBars) {
            if (maxP <= progressBars[progressBarsKey].p){
                maxP = progressBars[progressBarsKey].p;
                activeIndex = progressBarsKey;
            }
        }
        activeIndex = parseInt(activeIndex)
        console.log(activeIndex)
        if (activeIndex !== -1 && activeIndex !== progressBars.length -1 && containerRef.current && progressRefs.current[activeIndex]) {
            console.log('scrolling')
            const containerRect = containerRef.current.getBoundingClientRect();
            const progressRect = progressRefs.current[activeIndex]!.getBoundingClientRect();
            if (progressRect.top < containerRect.top || progressRect.bottom > containerRect.bottom) {
                progressRefs.current[activeIndex]!.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
    }, [progressBars, isIthProgressDone]);

    return (
        <Sider width="25%" style={siderStyle}>
            <div style={{
                height: "50px",
                margin: 0,
                padding: 0,
                textAlign: 'center',
                lineHeight: '50px',
                fontSize: 24,
            }}>Progress
            </div>
            <Flex
                vertical={true}
                style={{
                    overflow: "auto",
                    maxHeight: "calc(100% - 50px)",
                    height: "fit-content",
                    gap: '8px',
                    flexDirection: "column",
                    padding: "10px",
                }}
                ref={containerRef}
            >
                {progressBars.map((p, i) => (
                    <div key={p.index} ref={el => {
                        progressRefs.current[i] = el
                    }}>
                        {p.getProgressBar(i, isIthProgressDone)}
                    </div>
                ))}

            </Flex>
        </Sider>
    );
};

export default SiderComponent;
