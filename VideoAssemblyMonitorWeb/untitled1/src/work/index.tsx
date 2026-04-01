import React, {useState} from "react";
import {ConfigProvider, Flex, Layout, notification} from "antd";
import {ProgressBar} from "./entity/Progress.tsx";
import HeaderComponent from "./component/HeaderComponent.tsx";
import ContentComponent from "./component/content/ContentComponent.tsx";
import SiderComponent from "./component/SiderComponent.tsx";
import FooterComponent from "./component/FooterComponent.tsx";

const layoutStyle = {
    borderRadius: 8,
    backgroundColor: "#272727",
    overflow: 'hidden',
    width: '100%',
    maxWidth: '100%',
    height: '100vh',
    padding: '8px',
};

const Work: React.FC = () => {

    const [user, setUser] = useState("Liu");
    const [state, setState] = useState<'Waiting'|'Capturing'|'Reviewing'>('Waiting');
    const [api, contextHolder] = notification.useNotification();
    const [isProcessing, setIsProcessing] = useState<boolean>(false);  // Store the uploaded video URL
    const [progressBars, setProgressBars] = useState<ProgressBar[]>([]);


    return (

        <ConfigProvider
            theme={{
                token: {
                    colorText: "#000"
                }
            }}
        >
            <Flex style={{"padding": "0", color: "#242424"}}>
                <Layout style={layoutStyle}>
                    {contextHolder}
                    <HeaderComponent
                        state={state}
                        user={user}
                        setUser={setUser}
                        setState={setState}
                        api={api}
                        isProcessing={isProcessing}
                        setIsProcessing={setIsProcessing}
                        setProgressBars={setProgressBars}
                    />
                    <Layout style={{"backgroundColor": "#272727", "height": "60%"}}>
                        <ContentComponent
                            setState={setState}
                            user={user} state={state}
                            isProcessing={isProcessing}
                            setIsProcessing={setIsProcessing}
                            setProgressBars={setProgressBars}/>
                        <SiderComponent progressBars={progressBars} />
                    </Layout>
                    <FooterComponent user={user} state={state}/>
                </Layout>
            </Flex>
        </ConfigProvider>
    )
}

export default Work;