//
// MenuSider.tsx
//
import React, {JSX, useState} from "react";
import {ConfigProvider, Menu, MenuProps} from "antd";
import {DatabaseOutlined, SettingOutlined, BarChartOutlined} from '@ant-design/icons';
import SystemInfo from "./SystemInfo.tsx";
import ReviewTable from "./ReviewTable.tsx";
import {GeneralSettingPage} from "./GeneralSettingPage.tsx";
import {NetworkSettingsPage} from "./NetworkSettingsPage.tsx";
import {WarningAndQuotaPage} from "./WarningAndQuotaPage.tsx";
import {ModelSettingsPage} from "./ModelSettingsPage.tsx";
import { useLanguage } from "../../LanguageContext";
import PresetTable from "./PresetTable.tsx";

type MenuItem = Required<MenuProps>['items'][number];

interface MenuSiderProps {
    setCurrent: React.Dispatch<React.SetStateAction<JSX.Element>>
}

const MenuSider: React.FC<MenuSiderProps> = ({setCurrent: setPage}) => {
    const [current, setCurrent] = useState('stu');
    const { language } = useLanguage();

    // Map of sub-pages
    const pages: Map<string, React.JSX.Element> = new Map<string, React.JSX.Element>();
    pages.set('stu', <SystemInfo />);
    pages.set('wl', <ReviewTable />);
    pages.set('gen', <GeneralSettingPage />);
    pages.set('network', <NetworkSettingsPage />);
    pages.set('warn', <WarningAndQuotaPage />);
    pages.set('model', <ModelSettingsPage />);
    pages.set('ps', <PresetTable />);
    // Build our menu items from the language context
    const items: MenuItem[] = [
        {
            key: 'stu',
            label: language.menu.systemStatus,
            icon: <BarChartOutlined />
        },
        {
            key: 'db',
            label: language.menu.database,
            icon: <DatabaseOutlined />,
            children: [
                {key: 'wl', label: language.menu.workLog},
                {key: 'ps', label: language.menu.preset}
            ],
        },
        {
            key: 'sett',
            label: language.menu.settings,
            icon: <SettingOutlined />,
            children: [
                {key: 'gen', label: language.common.title},
                {key: 'network', label: language.network.pageTitle},
                {key: 'warn', label: language.warningAndQuota.pageTitle},
                {key: 'model', label: language.model.pageTitle}
            ],
        },
    ];

    const onClick: MenuProps['onClick'] = (e) => {
        setCurrent(e.key);
        const newVar = pages.get(e.key);
        setPage(newVar !== undefined ? newVar : <div/>);
    };

    return (
        <ConfigProvider
            theme={{
                components: {
                    Menu: {
                        groupTitleFontSize: 20,
                        fontSize: 16,
                        itemHeight: "60px"
                    },
                },
            }}
        >
            <Menu
                onClick={onClick}
                style={{ width: "100%", height: "100%" }}
                defaultOpenKeys={['stu']}
                selectedKeys={[current]}
                mode="inline"
                items={items}
            />
        </ConfigProvider>
    );
};

export default MenuSider;
