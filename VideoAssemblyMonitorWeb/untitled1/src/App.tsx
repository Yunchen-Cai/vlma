import '@ant-design/v5-patch-for-react-19';

import {Button} from "antd";
import {useNavigate} from "react-router";


function App() {
    const navigate = useNavigate();

    return (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', padding: 'auto', width: '100%',height: '100vh', alignItems: 'center' }}>
            <Button size="large" type="primary" style={{marginRight: "80px", padding:"60px", fontSize: 42}} onClick={() => navigate('/work')}>
                Work
            </Button>
            <Button size="large" type="default" style={{padding:"60px", fontSize: 42}} onClick={() => navigate('/manage')}>
                Manage
            </Button>
        </div>
    )
}

export default App
