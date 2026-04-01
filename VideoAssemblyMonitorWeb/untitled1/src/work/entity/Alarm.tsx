import {Alert, Badge} from "antd";

export class Alarm {
    message = 'Loading';
    percentage = 0
    description = "Loading description";
    type: "error" | "success" | "info" | "warning" | undefined = "error";
    badgeBackgroundColor = '#f5222d'
    getAlert(key: number){
        return (<Alert key={key}
            message={this.message}
            showIcon
            description={this.description}
            type={this.type}
            action={<Badge count={`${this.percentage}%`} color={this.badgeBackgroundColor}/>}
            style={{
                height: "auto",
                width: "240px",
            }}
        />)
    }

    constructor(message: string | undefined,
            description: string | undefined,
            percentage: number | undefined,
            type: "error" | "success" | "info" | "warning" | undefined){
        if (message != undefined) this.message = message;
        if (description != undefined) this.description = description;
        this.type = type;
        if (percentage != undefined) this.percentage = percentage;

        switch (this.type) {
            case "error":
                break
            case "success":
                this.badgeBackgroundColor = '#52c41a';
                break
            case "warning":
                this.badgeBackgroundColor = '#faad14';
                break
            case "info":
                this.badgeBackgroundColor = 'blue';
                break
        }
    }

}