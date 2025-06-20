import React from "react";
import { message, Button } from "antd";
import { useTranslation } from 'react-i18next';
import { useSearchParams } from "react-router-dom";
import s from './ConnectionPage.module.css'
import { ConnectionForm, OwnerQRModal, AdminPanel } from "../../components";
import { BACKEND_IP } from "../../shared";

interface BotInfo {
    botName: string;
    passUuid: string;
    botId: number;
    webUrl: string;
}

export const ConnectionPage: React.FC = () => {
    const { t, i18n } = useTranslation();
    const [searchParams] = useSearchParams();
    const [ref, setRef] = React.useState<string>("");
    const [bots, setBots] = React.useState<BotInfo[]>([]);
    const [selectedBot, setSelectedBot] = React.useState<BotInfo | null>(null);
    const [open, setOpen] = React.useState(false);
    const [showAdmin, setShowAdmin] = React.useState(false);
    const [loading, setLoading] = React.useState(false);

    React.useEffect(() => {
        const param = searchParams.get("ref") || "";
        setRef(param);
    }, [searchParams]);

    React.useEffect(() => {
        if (!ref) return;

        const fetchBots = async () => {
            try {
                const res = await fetch(`${BACKEND_IP}/owner/${ref}/bots`);
                if (!res.ok) return;
                const data = await res.json();
                const unique = data.filter(
                    (b: BotInfo, idx: number) =>
                        data.findIndex((other: BotInfo) => other.botId === b.botId) === idx
                );
                setBots(unique);
            } catch {
                /* ignore */
            }
        };

        fetchBots();
    }, [ref]);

    const selectBot = async (bot: BotInfo) => {
        setSelectedBot(bot);
        try {
            const vr = await fetch(`${BACKEND_IP}/${bot.botId}/isVerified`);
            const verified = await vr.json();
            setOpen(!verified);
            setShowAdmin(verified);
        } catch {
            /* ignore */
        }
    };

    const handleConnect = async (token: string): Promise<string | null> => {
        setLoading(true);
        try {
            const response = await fetch(`${BACKEND_IP}/bot`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    telegram_token: token,
                    owner_uuid: ref,
                    locale: i18n.language,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                let err = data.detail ?? t('failed_request');
                if (response.status === 401) {
                    err = t('invalid_token');
                }
                message.error(err);
                setLoading(false);
                return err;
            }

            const info: BotInfo = {
                botName: data.botName,
                passUuid: data.passUuid,
                botId: data.botId,
                webUrl: data.webUrl,
            };
            setBots((prev) => {
                if (prev.some((b) => b.botId === info.botId)) return prev;
                return [...prev, info];
            });
            setLoading(false);
            selectBot(info);
            return null;
        } catch (e) {
            const err = (e as Error).message;
            message.error(err);
            setLoading(false);
            return err;
        }
    };

    const handleLogout = async () => {
        if (!selectedBot) return;
        try {
            await fetch(`${BACKEND_IP}/bot/${selectedBot.botId}/logout`, { method: "PATCH" });
        } catch {
            /* ignore */
        }
        setShowAdmin(false);
        setSelectedBot(null);
    };

    const handleModalClose = () => {
        setOpen(false);
    };

    const handleModalVerified = () => {
        setOpen(false);
        setShowAdmin(true);
    };

    React.useEffect(() => {
        if (!showAdmin || !selectedBot) return;

        const unloadHandler = () => {
            fetch(`${BACKEND_IP}/bot/${selectedBot.botId}/logout`, {
                method: "PATCH",
                keepalive: true,
            }).catch(() => {/* ignore */});
        };

        window.addEventListener("beforeunload", unloadHandler);
        return () => {
            window.removeEventListener("beforeunload", unloadHandler);
            unloadHandler();
        };
    }, [showAdmin, selectedBot]);

    return(
        <div>
            {showAdmin && selectedBot ? (
                <AdminPanel onExit={handleLogout} botInfo={selectedBot} />
            ) : (
                <>
                    <div className={s.BotList}>
                        {bots.map((b) => (
                            <Button key={b.botId} type="primary" block style={{marginBottom: '10px'}} onClick={() => selectBot(b)}>
                                {b.botName}
                            </Button>
                        ))}
                    </div>
                    <div className={s.ConnectionFormWrapper}>
                        <ConnectionForm onConnect={handleConnect} loading={loading} />
                    </div>
                </>
            )}
            {selectedBot && (
                <OwnerQRModal
                    botName={selectedBot.botName}
                    uuid={ref}
                    botId={selectedBot.botId}
                    open={open}
                    onCancel={handleModalClose}
                    onVerified={handleModalVerified}
                />
            )}
        </div>
    )
}