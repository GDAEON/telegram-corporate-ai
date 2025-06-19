import React from "react";
import { ConnectionFormView } from "./ConnectionForm.view";

type Props = {
    onConnect: (token: string) => Promise<string | null>;
    loading: boolean;
};

export const ConnectionForm: React.FC<Props> = ({ onConnect, loading }) => {
    return(
        <ConnectionFormView onConnect={onConnect} loading={loading} />
    );
}