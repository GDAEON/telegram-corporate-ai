import React from "react";
import { Button, Modal, QRCode } from "antd";
import { useTranslation } from 'react-i18next';
import s from './OwnerQRModal.module.css'

type Props = {
    botName: string;
    uuid: string;
    open: boolean;
    onCancel: () => void;
};

export const OwnerQRModalView: React.FC<Props> = ({ botName, uuid, open, onCancel }) => {
    const { t } = useTranslation();
    return (
        <Modal
            open={open}
            onCancel={onCancel}
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
                <h1 style={{textAlign: "center"}}>{t('scan_qr')}</h1>
                <Button style={{height: "50px"}} block type="primary" size="large" onClick={() =>
                    window.open(
                    `https://t.me/${botName}?start=${uuid}`,
                    "_blank",
                    "noopener,noreferrer"
                    )
                }>{t('authorize')}</Button>
            </div>
        </Modal>
    );
};
