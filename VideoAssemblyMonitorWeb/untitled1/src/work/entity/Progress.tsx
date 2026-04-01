import {Badge, ConfigProvider, Flex, Progress} from "antd";

export class ProgressBar {
    constructor(index: number, name: string, quota: number, parent: number[], progress: number, p: number) {
        this.index = index;
        this.name = name;
        this.quota = quota;
        this.parent = parent;
        this.progress = progress;
        this.p = p;
    }

    index = 1
    name = 'loading name'
    quota = 5
    parent = [1,2]
    progress = 0.8
    p = 0


    public getProgressBar(key: number, isIthProgressDone: (i: number) => boolean) {
        return (
            <div key={key}  style={{width: "100%", flexDirection: "row"}} >

                    <ConfigProvider
                        theme={{
                            components: {
                                Progress: {
                                    remainingColor: '#444'
                                },
                            },
                        }}
                    ><Flex
                        vertical={true}
                        align="center"
                        gap={"5px"}
                        style={{
                            width: '100%',
                            padding: "10px",
                            backgroundColor: '#8A8A8A',
                            borderRadius: "15px",
                        }}
                    >
                        <Flex
                            vertical={false}
                            align="center"
                            justify={'flex-start'}
                            style={{
                                width: '100%',
                            }}
                        >
                            <Badge
                                count={`${this.p.toFixed(2)}%`}
                                showZero={false}
                                offset={[-20, 10]}
                                style={{
                                    backgroundColor: this.p<10? "#52c41a" : "#f5222d",
                                }}
                            ><div  style={{
                                margin: "10px",
                                marginRight: "20px",
                                width: "50px",
                                height: "50px",
                                borderRadius: "15px",
                                background: "#D9D9D9",
                                textAlign: "center",
                                lineHeight: "50px",
                                color: "#000",
                                fontSize: 20,
                            }}>
                                S{this.index}
                            </div></Badge>
                            <Flex
                                vertical={true}
                                align="flex-start"
                            >
                                <div style={{
                                    width: "fit-content",
                                    height: "40px",
                                    lineHeight: "40px",
                                    textAlign: "start",
                                    fontSize: 20,
                                }}>
                                    {this.name}
                                </div>
                                <Flex
                                    vertical={false}
                                    align="center"
                                    gap="5px"
                                    style={{
                                        width: "fit-content",
                                        height: "15px",
                                        lineHeight: "15px",
                                        textAlign: "start"
                                }}>
                                    after
                                    {this.parent.map((p) => {
                                        return (<div key={p} style={{
                                            margin: "2px",
                                            width: "20px",
                                            height: "20px",
                                            borderRadius: "10px",
                                            background: isIthProgressDone(p)? "#00ee00" :"#D9D9D9",
                                            textAlign: "center",
                                            lineHeight: "20px",
                                            color: "#000",
                                            fontSize: 12,
                                        }}>
                                            S{p}
                                        </div>)
                                })}
                                </Flex>
                            </Flex>
                            <div style={{
                                width: "fit-content",
                                height: "60px",
                                marginLeft: "auto",
                                marginRight: "15px",
                                lineHeight: "60px",
                                fontSize: 28,
                            }}>
                                {this.quota.toFixed(3)}s
                            </div>
                        </Flex>
                        <Progress
                            percent={Math.round(this.progress * 100)}
                            style={{
                                padding: "10px",
                                lineHeight: "15px",
                                width: '100%',
                            }}
                            percentPosition={{ align: 'center', type: 'inner' }}
                            size={['100%', 20]}
                        />
                    </Flex></ConfigProvider>

            </div>
        )
    }

}