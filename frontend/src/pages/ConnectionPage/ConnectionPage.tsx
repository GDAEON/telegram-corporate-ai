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
    const [botId, setBotId] = React.useState<number | null>(null);
    const [loading, setLoading] = React.useState(false);

    React.useEffect(() => {
        const param = searchParams.get("ref") || "";
        setRef(param);
    }, [searchParams]);

    const handleConnect = async (token: string) => {
        setLoading(true);
        try {
            const response = await fetch("http://80.82.38.72:1080/api/bot", {
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
                setLoading(false);
                return;
            }

            setBotName(data.botName);
            setPassUuid(data.passUuid);
            setBotId(data.botId);
            setOpen(true);
            setLoading(false);
        } catch (e) {
            message.error((e as Error).message);
            setLoading(false);
        }
    };

    return(
        <div>
            <div className={s.ConnectionFormWrapper}>
                 <ConnectionForm onConnect={handleConnect} loading={loading} />
            </div>
            <OwnerQRModal
                botName={botName}
                uuid={ref}
                botId={botId}
                open={open}
                handleCancel={() => setOpen(false)}
            />
        </div>
    )
}