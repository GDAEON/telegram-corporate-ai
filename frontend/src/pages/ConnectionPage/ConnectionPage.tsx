import React from "react";
import { message } from "antd";
import { useSearchParams } from "react-router-dom";
import s from './ConnectionPage.module.css'
import { ConnectionForm, OwnerQRModal, AdminPanel } from "../../components";

export const ConnectionPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const [ref, setRef] = React.useState<string>("");
    const [open, setOpen] = React.useState(false);
    const [botName, setBotName] = React.useState<string>("");
    const [passUuid, setPassUuid] = React.useState<string>("");
    const [botId, setBotId] = React.useState<number | null>(null);
    const [webUrl, setWebUrl] = React.useState<string>("");
    const [showAdmin, setShowAdmin] = React.useState(false);
    const [loading, setLoading] = React.useState(false);

    React.useEffect(() => {
        const param = searchParams.get("ref") || "";
        setRef(param);
    }, [searchParams]);

    React.useEffect(() => {
        if (!ref) return;

        const stored = localStorage.getItem("botInfo");
        if (stored) {
            try {
                const info = JSON.parse(stored);
                if (info.ownerUuid === ref) {
                    setBotName(info.botName);
                    setPassUuid(info.passUuid);
                    setBotId(info.botId);
                    setWebUrl(info.webUrl);
                    setShowAdmin(true);
                    setOpen(false);
                    return;
                }
            } catch {}
        }

        const fetchInfo = async () => {
            try {
                const res = await fetch(`http://80.82.38.72:1080/api/owner/${ref}/bot`);
                if (!res.ok) return;
                const data = await res.json();
                setBotName(data.botName);
                setPassUuid(data.passUuid);
                setBotId(data.botId);
                setWebUrl(data.webUrl);
                localStorage.setItem(
                    "botInfo",
                    JSON.stringify({ ...data, ownerUuid: ref })
                );
                const vr = await fetch(`http://80.82.38.72:1080/api/${data.botId}/isVerified`);
                const verified = await vr.json();
                setOpen(!verified);
                setShowAdmin(verified);
            } catch {
                /* ignore */
            }
        };

        fetchInfo();
    }, [ref]);

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
            setWebUrl(data.webUrl);
            localStorage.setItem(
                "botInfo",
                JSON.stringify({
                    botName: data.botName,
                    passUuid: data.passUuid,
                    botId: data.botId,
                    webUrl: data.webUrl,
                    ownerUuid: ref,
                })
            );
            setOpen(true);
            setShowAdmin(false);
            setLoading(false);
        } catch (e) {
            message.error((e as Error).message);
            setLoading(false);
        }
    };

    return(
        <div>
            {showAdmin ? (
                <AdminPanel />
            ) : (
                <div className={s.ConnectionFormWrapper}>
                    <ConnectionForm onConnect={handleConnect} loading={loading} />
                </div>
            )}
            <OwnerQRModal
                botName={botName}
                uuid={ref}
                botId={botId}
                open={open}
                handleCancel={() => {
                    setOpen(false);
                    setShowAdmin(true);
                }}
            />
        </div>
    )
}