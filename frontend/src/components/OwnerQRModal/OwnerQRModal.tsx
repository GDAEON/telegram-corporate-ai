import React, { useEffect } from "react";
import { OwnerQRModalView } from "./OwnerQRModal.view";

type Props = {
    botName: string;
    uuid: string;
    open: boolean;
    botId: number | null;
    handleCancel: () => void;
};

export const OwnerQRModal: React.FC<Props> = ({ botName, uuid, botId, open, handleCancel }) => {

    useEffect(() => {
        if (!open) return;

        const checkVerification = async () => {
            const res = await fetch(`http://80.82.38.72:1080/api/${botId}/isVerified`);
            const verified = await res.json();
            if (verified) {
                handleCancel();
            }
        };

        checkVerification();                          
        const timer = setInterval(checkVerification, 3000);
        return () => clearInterval(timer);
    }, [open, botId, handleCancel]);
    
    return (
        <OwnerQRModalView botName={botName} uuid={uuid} open={open} handleCancel={handleCancel} />
    );
};
