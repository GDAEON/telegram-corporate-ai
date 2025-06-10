import React, { useState } from "react";
import { Modal, QRCode} from "antd"

type Props = {
    botName: string;
    uuid: string;
}

export const OwnerQRModalView: React.FC<Props> = ({botName, uuid}) => {

    const [open, setOpen] = useState(false);

    const showModal = () => {
        setOpen(true);
    };

    const handleCancel = () => {
        setOpen(false);
    };

    return(
        <Modal
        open={open}
        onCancel={handleCancel}
        footer={[]}
        >
            <QRCode value={`https://t.me/${botName}?start=${uuid}`} />
            <h1>Scan the QR code to authorize in the bot</h1>
        </Modal>
    );
};