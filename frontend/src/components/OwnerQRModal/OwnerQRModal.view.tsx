import React from "react";
import { Button, Modal, QRCode } from "antd";
import s from './OwnerQRModal.module.css'

type Props = {
    botName: string;
    uuid: string;
    open: boolean;
    handleCancel: () => void;
};

export const OwnerQRModalView: React.FC<Props> = ({ botName, uuid, open, handleCancel }) => {
    return (
        <Modal
            open={open}
            onCancel={handleCancel}
            footer={[]}
            centered
            width={{
                xs: '90%',
                sm: '80%',
                md: '70%',
                lg: '60%',
                xl: '50%',
                xxl: '40%',
            }}
        >
            <div className={s.qrCodeWrapper}>
                <QRCode size={300} icon={"/telegram-icon.svg"} iconSize={40} value={`https://t.me/${botName}?start=${uuid}`} />
                <h1 style={{textAlign: "center"}}>Scan the QR code or click the button below to authorize in the bot</h1>
                <Button style={{height: "50px"}} block type="primary" size="large" onClick={() =>
                    window.open(
                    `https://t.me/${botName}?start=${uuid}`,
                    "_blank",
                    "noopener,noreferrer"
                    )
                }>Authorize</Button>
            </div>
        </Modal>
    );
};
