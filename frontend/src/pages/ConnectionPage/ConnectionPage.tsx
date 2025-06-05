import React from "react";
import s from './ConnectionPage.module.css'
import { ConnectionForm } from "../../components";

export const ConnectionPage: React.FC = () => {
    return(
        <div>
            <div className={s.ConnectionFormWrapper}>
                <ConnectionForm/>
            </div>
        </div>
    )
}