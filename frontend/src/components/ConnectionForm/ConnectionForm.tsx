import React from "react";
import { ConnectionFormView } from "./ConnectionForm.view";

type Props = {
    onConnect: () => void;
};

export const ConnectionForm: React.FC<Props> = ({ onConnect }) => {
    return(
        <ConnectionFormView onConnect={onConnect} />
    );
}