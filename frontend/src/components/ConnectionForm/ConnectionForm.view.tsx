import React from "react";
import type { FormProps } from "antd";
import { Button, Form, Input } from "antd";
import { useTranslation } from 'react-i18next';
import s from "./ConnectionForm.module.css";

type FieldType = {
  token?: string;
};



const onFinishFailed: FormProps<FieldType>["onFinishFailed"] = (errorInfo) => {
  console.log("Failed:", errorInfo);
};

export const ConnectionFormView: React.FC<{ onConnect: (token: string) => void; loading: boolean }> = ({ onConnect, loading }) => {
  const { t } = useTranslation();

  const onFinish: FormProps<FieldType>["onFinish"] = values => {
        onConnect(values.token ?? "");                
  };

  return (
    <div className={s.pageContainer}>
      <h1 className={s.FormTitle}>{t('connect_bot')}</h1>
      <Form
        style={{ width: "100%" }}
        onFinish={onFinish}
        onFinishFailed={onFinishFailed}
        initialValues={{ remember: true }}
      >
        <Form.Item<FieldType>
          name="token"
          rules={[
            { required: true, message: t('token_required') },
          ]}
        >
          <Input style={{height: "50px"}} placeholder={t('token_placeholder')} disabled={loading} />
        </Form.Item>

        <Form.Item>
          <Button style={{height: "50px"}} block type="primary" size="large" htmlType="submit" loading={loading} disabled={loading}>
            {t('connect')}
          </Button>
        </Form.Item>
      </Form>

      <div className={s.container}>
      <h3>{t('how_to_obtain')}</h3>
      <ol className={s.list}>
        <li>{t('step_botfather')}</li>
        <li>
          {t('step_newbot')}
        </li>
        <li>{t('step_copy_token')}</li>
      </ol>

      <div className={s.tip + " " + s.tip1} dangerouslySetInnerHTML={{__html: t('tip_search_botfather')}} />
      <div className={s.tip + " " + s.tip2}>{t('tip_command')}</div>
      <div className={s.tip + " " + s.tip3} dangerouslySetInnerHTML={{__html: t('tip_token_example')}} />
    </div>

    </div>
  );
};
