//
// NetworkSettingsPage.tsx
//
// 网络设置页面：包括管理界面Host/Port、Eoid Host/Port、Roboflow Host/Port
// 提供测试按钮
//

import React, {useEffect, useState} from "react";
import { Input, InputNumber, Button, Form, message } from "antd";
import { useLanguage } from "../../LanguageContext";
import { Typography } from 'antd';
import {getAllConfigs, HostAndPort, ping, pingRf, updateRoboflowConfig} from "../services/configAPI.ts";

const { Title } = Typography;

export const NetworkSettingsPage: React.FC = () => {
    const { language } = useLanguage();
    const [form] = Form.useForm();
    const [pingBe, setPingBe] = useState<boolean>(false);
    const [beTested, setBeTested] = useState<boolean>(false);
    const [beTestResult, setBeTestResult] = useState<boolean>(false);

    const [pingRoboflow, setPingRoboflow] = useState<boolean>(false);
    const [rfTested, setRfTested] = useState<boolean>(false);
    const [rfTestResult, setRfTestResult] = useState<boolean>(false);

    // 示例：管理界面、Eoid、Roboflow 的 host / port
    interface NetworkFormValues {
        managementHost: string;
        managementPort: number;
        roboflowHost: string;
        roboflowPort: number;
    }

    const initialValues: NetworkFormValues = {
        managementHost: "http://localhost",
        managementPort: 8080,
        roboflowHost: "http://localhost",
        roboflowPort: 9001,
    };

    // 演示：从后端 /config/all 拉取当前配置来填充表单
    useEffect(() => {
        const fetchConfigs = async () => {
            try {
                const allConfigs = await getAllConfigs();
                // eoidHost 和 eoidPort 对应后端 pythonServerHost / pythonServerMainPort
                // roboflowHost 和 roboflowPort 对应后端 roboflowHost / roboflowPort
                form.setFieldsValue({
                    managementHost: "http://localhost", // 后端无此字段，仅示例
                    managementPort: 8080,               // 后端无此字段，仅示例
                    eoidHost: allConfigs.pythonServerHost,
                    eoidPort: Number(allConfigs.pythonServerMainPort),
                    roboflowHost: allConfigs.roboflowHost,
                    roboflowPort: Number(allConfigs.roboflowPort),
                });
            } catch (error) {
                message.error("Failed to fetch config: " + String(error));
            }
        };
        fetchConfigs();
    }, [form]);

    const handleFinish = async (values: NetworkFormValues) => {
        try {

            // 1) 更新 Roboflow
            const roboflowRequest: HostAndPort = {
                host: values.roboflowHost,
                port: String(values.roboflowPort),
            };
            await updateRoboflowConfig(roboflowRequest);

            // managementHost/Port 仅示例，本后端暂未提供相关接口
            message.success("Network settings saved successfully!");
        } catch (error) {
            message.error("Failed to save network settings: " + String(error));
        }
    };

    function handleTestBackend() {
        setPingBe(true);

        ping().then((result) => {
            setBeTested(true);
            setBeTestResult(result);
            setPingBe(false);
        })
    }

    function handleTestRoboflow() {
        setPingRoboflow(true);

        pingRf(form.getFieldValue("roboflowHost"), form.getFieldValue("roboflowPort")).then((result) => {
            setRfTested(true);
            setRfTestResult(result);
            setPingRoboflow(false);
        })
    }

    return (
        <div style={{ marginTop: 36, padding: "24px 60px" }}>
            <Title>{language.network.pageTitle}</Title>

            <Form
                form={form}
                onFinish={handleFinish}
                initialValues={initialValues}
                layout="vertical"
                style={{ marginTop: 36 }}
            >
                <Form.Item
                    label={language.network.managementHostLabel}
                    name="managementHost"
                    rules={[{ required: true, message: "Please input management host" }]}
                >
                    <Input style={{ width: 300 }} />
                </Form.Item>

                <Form.Item
                    label={language.network.managementPortLabel}
                    name="managementPort"
                    rules={[{ required: true, message: "Please input management port" }]}
                >
                    <InputNumber style={{ width: 300 }} />
                </Form.Item>

                <Form.Item>
                    <Button
                        style={{ marginRight: 24 }}
                        onClick={() => handleTestBackend()}
                        loading={pingBe}
                        variant={beTested ? "filled" : undefined}
                        color={beTested ? (beTestResult ? 'cyan' : 'danger') : undefined}
                    >
                        {language.network.testButton}
                    </Button>
                </Form.Item>

                <Form.Item
                    label={language.network.roboflowHostLabel}
                    name="roboflowHost"
                    rules={[{ required: true, message: "Please input Roboflow host" }]}
                >
                    <Input style={{ width: 300 }} />
                </Form.Item>

                <Form.Item
                    label={language.network.roboflowPortLabel}
                    name="roboflowPort"
                    rules={[{ required: true, message: "Please input Roboflow port" }]}
                >
                    <InputNumber style={{ width: 300 }} />
                </Form.Item>

                <Form.Item>
                    <Button
                        style={{ marginRight: 24 }}
                        onClick={() => handleTestRoboflow()}
                        loading={pingRoboflow}
                        variant={rfTested ? "filled" : undefined}
                        color={rfTested ? (rfTestResult ? 'cyan' : 'danger') : undefined}
                    >
                        {language.network.testButton}
                    </Button>
                </Form.Item>

                <Form.Item style={{ marginLeft: "auto" }}>
                    <Button type="primary" htmlType="submit">
                        {language.network.submit}
                    </Button>
                </Form.Item>
            </Form>
        </div>
    );
};
