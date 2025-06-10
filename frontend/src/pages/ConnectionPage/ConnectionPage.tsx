import React from "react";
import s from './ConnectionPage.module.css'
import { ConnectionForm, OwnerQRModal } from "../../components";

export const ConnectionPage: React.FC = () => {
    const [open, setOpen] = React.useState(false);

    return(
        <div>
            <div className={s.ConnectionFormWrapper}>
                <ConnectionForm onConnect={() => setOpen(true)} />
            </div>
            <OwnerQRModal
                botName="corporate_ai_bot"
                uuid="ueiue"
                open={open}
                handleCancel={() => setOpen(false)}
            />
        </div>
    )
}