import React, { useEffect } from "react";
import { OwnerQRModalView } from "./OwnerQRModal.view";
import { BACKEND_IP } from "../../shared";

type Props = {
    botName: string;
    uuid: string;
    open: boolean;
    botId: number | null;
    onCancel: () => void;
    onVerified: () => void;
};

export const OwnerQRModal: React.FC<Props> = ({ botName, uuid, botId, open, onCancel, onVerified }) => {

    useEffect(() => {
        if (!open) return;

        const checkVerification = async () => {
            const res = await fetch(`${BACKEND_IP}/${botId}/isVerified`);
            const verified = await res.json();
            if (verified) {
                onVerified();
            }
        };

        checkVerification();
        const timer = setInterval(checkVerification, 3000);
        return () => clearInterval(timer);
    }, [open, botId, onVerified]);
    
    return (
        <OwnerQRModalView botName={botName} uuid={uuid} open={open} onCancel={onCancel} />
    );
};
