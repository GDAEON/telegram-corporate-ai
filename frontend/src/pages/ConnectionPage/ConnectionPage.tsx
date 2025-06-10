import React from "react";
import { message } from "antd";
import { useSearchParams } from "react-router-dom";
import s from './ConnectionPage.module.css'
import { ConnectionForm, OwnerQRModal } from "../../components";

export const ConnectionPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const [ref, setRef] = React.useState<string>("");
    const [open, setOpen] = React.useState(false);
    const [botName, setBotName] = React.useState<string>("");
    const [passUuid, setPassUuid] = React.useState<string>("");

    React.useEffect(() => {
        const param = searchParams.get("ref") || "";
        setRef(param);
    }, [searchParams]);

    const handleConnect = async (token: string) => {
        try {
            const response = await fetch("http://localhost:8000/api/bot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    telegram_token: token,
                    owner_uuid: ref,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                message.error(data.detail ?? "Request failed");
                return;
            }

            setBotName(data.botName);
            setPassUuid(data.passUuid);
            setOpen(true);
        } catch (e) {
            message.error((e as Error).message);
        }
    };

    return(
        <div>
            <div className={s.ConnectionFormWrapper}>
                <ConnectionForm onConnect={handleConnect} />
            </div>
            <OwnerQRModal
                botName={botName}
                uuid={passUuid}
                open={open}
                handleCancel={() => setOpen(false)}
            />
        </div>
    )
}