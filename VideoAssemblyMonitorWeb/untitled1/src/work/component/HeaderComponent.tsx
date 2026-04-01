import {Button, Flex, Input, Modal} from "antd";
import React, {Dispatch, SetStateAction, useCallback, useState} from "react";
import {Header} from "antd/es/layout/layout";
import axios from "axios";
import { CloseCircleFilled } from '@ant-design/icons';
import {NotificationInstance} from "antd/es/notification/interface";
import {ProgressBar} from "../entity/Progress.tsx";
import {host} from "../../Share.tsx";

const headerStyle: React.CSSProperties = {
    margin: '8px',
    textAlign: 'left',
    fontSize: '36px',
    color: '#fff',
    height: 64,
    paddingInline: 48,
    lineHeight: '64px',
    backgroundColor: '#A3A3A3',
    borderRadius: 15,
};

interface Props {
    state: 'Waiting'|'Capturing'|'Reviewing';
    user: string;
    setUser: (user: string) => void;
    setState: Dispatch<SetStateAction<'Waiting'|'Capturing'|'Reviewing'>>;
    api: NotificationInstance;
    isProcessing: boolean
    setIsProcessing: Dispatch<SetStateAction<boolean>>;
    setProgressBars: Dispatch<SetStateAction<ProgressBar[]>>;
}

export const HeaderComponent: React.FC<Props> = ({ state, user, setUser , setState, api, isProcessing, setIsProcessing, setProgressBars }) => {

    let userSetting = "";

    const [isModalOpen, setIsModalOpen] = useState(false);

    const [isStopping, setIsStopping] = useState(false);


    const showModal = () => {
        setIsModalOpen(true);
    };

    const handleOk = () => {
        setUser(userSetting);
        setIsModalOpen(false);
    };

    const handleCancel = () => {
        userSetting = "";
        setIsModalOpen(false);
    };

    const handleStop = useCallback(() => {
        setProgressBars([])
        if (state === 'Waiting') {
            if (isProcessing) {
                axios.get(`${host}/interrupt?user=${user}`)
                    .then(() => {
                        setIsStopping(false);
                        setState("Waiting");
                        setIsProcessing(false);
                    })
                    .catch((error: string) => {
                        setIsStopping(false);
                        api.open({
                            message: 'Error requesting stop',
                            description: error,
                            icon: <CloseCircleFilled style={{ color: '#108ee9' }} />,
                        });
                    });
                return
            }
            setIsStopping(false);
        } else {
            axios.get(`${host}/interrupt?user=${user}`)
                .then(() => {})
                .catch((error: string) => {
                    setIsStopping(false);
                    api.open({
                        message: 'Error requesting stop',
                        description: error,
                        icon: <CloseCircleFilled style={{ color: '#108ee9' }} />,
                    });
                });
            if (state === 'Capturing') {
                setIsStopping(false);
                setState("Waiting");
            } else if (state === 'Reviewing') {
                setIsStopping(false);
                setState("Waiting");
            }
        }
    }, [state, user, isProcessing])


    return <Header style={headerStyle}>

        <Flex vertical={false} justify="flex-start" style={{alignItems: "center"}}>
            <div style={{fontSize: 30, alignContent: "center"}}>Video Assembly Monitor System</div>
            <div
                style={{
                    width: "2px",  // 设置矩形的宽度
                    height: "34px",  // 设置矩形的高度
                    backgroundColor: "#fff", // 设置矩形的颜色
                    margin: "0 20px",
                    borderRadius: 2,
                }}
            ></div>
            <HeaderStateWords state={state}/>
            <Button
                danger
                type="primary"
                loading={isStopping}
                style={{
                    visibility: state === "Waiting" && !isProcessing ? "hidden": "visible",
                    margin: "3px 10px",
                    padding: '10px 15px',
                    fontSize: 20,
                    textAlign: 'end',
                    borderColor: "white",
                    border: "2px solid white",
                    borderRadius: "15px",
                    height: "40px",
                    lineHeight: "15px"
                }}
                onClick={() => {setIsStopping(true);handleStop()}}
            >Stop</Button>

            <div style={{marginLeft: "auto", fontSize: 24, alignItems: "center"}}>
                Hi, {user}!
                <Button style={{"borderRadius": "8", marginLeft: 20}} ghost onClick={showModal}>Change
                    Name</Button>
                <Modal title="Name Reset" open={isModalOpen} onOk={handleOk}
                       onCancel={handleCancel}>
                    <p>Enter a new name</p>
                    <Input placeholder="Enter a new name"
                           onChange={t => userSetting = t.target.value}/>
                </Modal>
            </div>
        </Flex>
    </Header>;
}

interface PropsOfHeaderStateWords {
    state: 'Waiting' | 'Capturing' | 'Reviewing';
}

const HeaderStateWords: React.FC<PropsOfHeaderStateWords> = ({state}) => {

    if (state === "Waiting") {
        return (
            <div
                style={{
                margin: "3px",
                padding: "10px",
                fontSize: 24,
                textAlign: "end",
                borderColor: "transparent",
                border: "transparent",
                borderRadius: "0px",
                height: "40px",
                lineHeight: "20px"
            }}>{state}</div>
        )
    } else {
        return (<div style={{
            margin: "3px",
            padding: '10px',
            fontSize: 24,
            textAlign: 'end',
            borderColor: "white",
            border: "2px solid white",
            borderRadius: "15px",
            height: "40px",
            lineHeight: "15px"
        }}>{state}</div>
        )
    }
}

export default HeaderComponent;