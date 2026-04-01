//
// CommonPage.tsx
//
// 通用页面：设置语言、重启后端服务器、关闭后端服务器
//

import React, {useEffect, useState} from "react";
import {Button, Modal, Select, message, App} from "antd";
import { useLanguage } from "../../LanguageContext";
import { Typography } from 'antd';
import axios from "axios";
import {host} from "../../Share.tsx";
import {ping} from "../services/configAPI.ts";

const { Title } = Typography;

const { Option } = Select;

export const GeneralSettingPage: React.FC = () => {
    const { language, currentLangKey, changeLanguage } = useLanguage();
    const [modal, contextHolder] = Modal.useModal();

    // 用于存储后端是否在线的状态
    const [isOnline, setIsOnline] = useState(true);

    // 每 0.2s 执行一次心跳检查，调用 ping() 判断后端是否在线
    useEffect(() => {
        const intervalId = setInterval(() => {
            ping().then((res) => {
                setIsOnline(res); // 后端在线时，res = true
            })
            .catch(() => {
                setIsOnline(false); // 若请求失败，说明后端不在线
            });
        }, 200); // 0.2s

        // 组件卸载时清理定时器
        return () => clearInterval(intervalId);
    }, []);

    // 处理选择语言
    const handleChangeLanguage = (value: string) => {
        changeLanguage(value);
        message.success(`Language changed to ${value}`);
    };

    // 重启后端服务器
    const handleRestart = () => {
        modal.confirm({
            title: language.common.restartBackendConfirmTitle,
            okText: language.common.confirmOk,
            cancelText: language.common.confirmCancel,
            onOk: () => {
                axios
                    .get(host + "/management/hot-reload")
                    .then(() => {
                        console.log("Restart command sent to server");
                    })
                    .catch((error) => {
                        console.log(`Error restarting server: ${error}`);
                    });
                console.log("restarting backend server...");
            },
        });
    };

    // 关闭后端服务器
    const handleClose = () => {
        modal.confirm({
            title: language.common.closeBackendConfirmTitle,
            okText: language.common.confirmOk,
            cancelText: language.common.confirmCancel,
            onOk: () => {
                axios
                    .get(host + "/management/shutdown")
                    .then(() => {
                        message.info("Closing backend server...");
                    })
                    .catch((error) => {
                        message.error(`Error shutting down server: ${error.message}`);
                    });
                message.info("Closing backend server...");
            },
        });
    };

    return (
        <div style={{ marginTop: 36, padding: "24px 60px"}}>
            {contextHolder}
            <Title>{language.common.title}</Title>
            <div style={{ marginBottom: 48, marginTop: 24 }}>
                <label style={{ marginRight: 12 }}>
                    {language.common.languageSelectLabel}:
                </label>
                <Select
                    style={{ width: 200 }}
                    value={currentLangKey}
                    onChange={handleChangeLanguage}
                    placeholder={language.common.languageSelectPlaceholder}
                >
                    <Option value="en">English</Option>
                    <Option value="zh">简体中文</Option>
                    <Option value="zh_tr">繁體中文</Option>
                    <Option value="ja">日本語</Option>
                    <Option value="fr">Français</Option>
                    <Option value="de">Deutsch</Option>
                    <Option value="ru">Русский</Option>
                    <Option value="ko">한국어</Option>
                    <Option value="ar">العربية</Option>
                </Select>
            </div>

            <div style={{ marginBottom: 24 }}>
                <App><Button danger onClick={handleRestart} disabled={!isOnline}>
                    {language.common.restartBackendLabel}
                </Button></App>
            </div>

            <div>
                <App><Button danger onClick={handleClose} disabled={!isOnline}>
                    {language.common.closeBackendLabel}
                </Button></App>
            </div>
        </div>
    );
};
