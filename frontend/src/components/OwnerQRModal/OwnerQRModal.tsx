import React, { useState } from "react";
import { OwnerQRModalView } from "./OwnerQRModal.view";

type Props = {
    botName: string;
    uuid: string;
    open: boolean;
    handleCancel: () => void;
};

export const OwnerQRModal: React.FC<Props> = ({ botName, uuid, open, handleCancel }) => {
    return (
        <OwnerQRModalView botName={botName} uuid={uuid} open={open} handleCancel={handleCancel} />
    );
};
