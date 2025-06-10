import React from "react";
import { Modal, QRCode} from "antd"

type Props = {
    botName: string;
    uuid: string;
    open: boolean;
    handleCancel: () => void;
}

export const OwnerQRModalView: React.FC<Props> = ({botName, uuid, open, handleCancel}) => {
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