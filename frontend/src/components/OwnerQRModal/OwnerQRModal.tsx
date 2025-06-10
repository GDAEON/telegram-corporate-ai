import React, { useState } from "react";
import { OwnerQRModalView } from "./OwnerQRModal.view";

type Props = {
    open: boolean
}

export const OwnerQRModal: React.FC = () => {
    const [open, setOpen] = useState(false);

    // const showModal = () => {
    //     setOpen(true);
    // };

    const handleCancel = () => {
        setOpen(false);
    };

    return(
        <OwnerQRModalView botName="corporate_ai_bot" uuid="ueiue" open={open} handleCancel={handleCancel} />
    );
};