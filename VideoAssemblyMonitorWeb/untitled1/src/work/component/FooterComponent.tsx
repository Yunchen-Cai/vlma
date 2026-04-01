import {useEffect, useState} from 'react';
import { Flex } from 'antd';
import {Alarm} from "../entity/Alarm.tsx";
import axios from "axios";
import {Footer} from "antd/es/layout/layout";

import {bgColorOfElement1, host} from "../../Share.tsx";

interface FooterProps {
    state: 'Waiting'|'Capturing'|'Reviewing';
    user: string;
}

const footerStyle: React.CSSProperties = {
    margin: '8px',
    justifyItems: 'flex-start',
    alignItems: 'flex-start',
    color: '#fff',
    backgroundColor: bgColorOfElement1,
    borderRadius: 15,
    height: "25vh",
};

const FooterComponent: React.FC<FooterProps> = ({ state, user }) => {

    const [alarms, setAlarms] = useState<Alarm[]>([]);

    useEffect(() => {
        const intervalId = setInterval(() => {
            if (state === 'Waiting') {
                setAlarms([])
                return
            }
            // Fetch alarms and progress bars
            axios.get(`${host}/alarm?name=${user}`)
                .then((response: { data: Alarm[]; }) => {
                    setAlarms((response.data)?.map((alarm: Alarm) => {
                        return new Alarm(alarm.message, alarm.description, parseFloat(alarm.percentage.toFixed(2)), alarm.type);
                    }));
                })
                .catch((error: string) => console.error("Error fetching alarms", error));
        }, 500);  // 500ms interval to fetch data

        // Clean up the interval on component unmount
        return () => clearInterval(intervalId);
    }, [user, state]);


    return (
        <Footer style={footerStyle}>
            <Flex vertical={true} justify={'flex-start'} style={{ height: '100%', width: '100%' }}>
                <div color={'#fff'} style={{
                    height: 50,
                    margin: 0,
                    padding: 0,
                    textAlign: 'left',
                    lineHeight: '50px',
                    fontSize: 24,
                }}>Alarm</div>
                <Flex color={'#fff'} vertical={false} style={{
                    flex: 1,
                    margin: 0,
                    padding: '20px 0',
                    gap: '20px',
                }}>
                    {alarms.map((alarm, i) => alarm.getAlert(i))}
                </Flex>
            </Flex>
        </Footer>
    );
};

export default FooterComponent;
