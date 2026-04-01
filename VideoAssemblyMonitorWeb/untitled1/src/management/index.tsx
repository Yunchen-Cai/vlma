import React, {useState} from "react";
import {Layout} from "antd";
import {Content, Footer, Header} from "antd/es/layout/layout";
import Sider from "antd/es/layout/Sider";
import {bgColorOfElement1, bgColorOfElement2} from "../Share.tsx";
import MenuSider from "./component/Menu.tsx";
import SystemInfo from "./component/SystemInfo.tsx";


const layoutStyle = {
    borderRadius: 8,
    backgroundColor: bgColorOfElement2,
    overflow: 'hidden',
    width: '100%',
    maxWidth: '100%',
    height: '100vh',
    padding: '8px',

};

const headerStyle: React.CSSProperties = {
    margin: '8px',
    textAlign: 'left',
    fontSize: '36px',
    color: '#333',
    height: 64,
    paddingInline: 48,
    lineHeight: '64px',
    backgroundColor: '#eee',
    borderRadius: 15,
    boxShadow: '0 0 .4em #666',

};

const siderStyle: React.CSSProperties = {
    marginLeft: '8px',
    textAlign: 'center',
    lineHeight: '120px',
    color: '#fff',
    backgroundColor: bgColorOfElement1,
    borderRadius: 15,
    overflow: 'hidden',
    boxShadow: '0 0 .4em #999',
};

const contentStyle: React.CSSProperties = {
    margin: "0 8px",
    textAlign: "left",
    color: "#000",
    backgroundColor: "#fff",
    borderRadius: 15,
    overflow: "auto", // Prevent anything from exceeding the boundaries
    boxShadow: '0 0 .4em #999',
};

const footerStyle: React.CSSProperties = {
    margin: '8px',
    justifyItems: 'flex-start',
    alignItems: 'flex-start',
    color: '#fff',
    backgroundColor: "#ddd",
    borderRadius: 15,
    height: "3vh",
    boxShadow: '0 0 .4em #aaa',

};

/**
 *  * @constructor
 */
const Management: React.FC = () => {


    const [current, setCurrent] = useState((<SystemInfo />));

    return (


        <Layout style={layoutStyle}>
            <Header style={headerStyle}>Video Monitor Management Dashboard</Header>
            <Layout style={{"backgroundColor": bgColorOfElement2}}>
                <Sider width="240px" style={siderStyle}>
                    <MenuSider setCurrent={setCurrent}/>
                </Sider>
                <Content style={contentStyle}>
                    {current}
                </Content>
            </Layout>
            <Footer style={footerStyle}></Footer>

        </Layout>

    )
}


export default Management;