import React from "react";
import type { FormProps } from "antd";
import { Button, Form, Input } from "antd";
import s from "./ConnectionForm.module.css";

type FieldType = {
  token?: string;
};



const onFinishFailed: FormProps<FieldType>["onFinishFailed"] = (errorInfo) => {
  console.log("Failed:", errorInfo);
};

export const ConnectionFormView: React.FC<{ onConnect: () => void }> = ({ onConnect }) => {

  const onFinish: FormProps<FieldType>["onFinish"] = values => {
        console.log("Success:", values);
        onConnect();                
  };

  return (
    <div className={s.pageContainer}>
      <h1 className={s.FormTitle}>Connect Telegram Bot</h1>
      <Form
        style={{ width: "100%" }}
        onFinish={onFinish}
        onFinishFailed={onFinishFailed}
        initialValues={{ remember: true }}
      >
        <Form.Item<FieldType>
          name="token"
          rules={[
            { required: true, message: "Please input telegram bot token" },
          ]}
        >
          <Input style={{height: "50px"}} placeholder="Paste your bot token here..." />
        </Form.Item>

        <Form.Item>
          <Button style={{height: "50px"}} block type="primary" size="large" htmlType="submit">
            Connect
          </Button>
        </Form.Item>
      </Form>

      <div className={s.container}>
      <h3>How to obtain a bot token:</h3>
      <ol className={s.list}>
        <li>On Telegram, open a chat with <br /> the BotFather.</li>
        <li>
          Send the <code>/newbot</code> command and <br /> follow the instructions.
        </li>
        <li>Copy the token shown <br /> in the response.</li>
      </ol>

      <div className={s.tip + " " + s.tip1}>Search for<br /><strong>“BotFather”</strong></div>
      <div className={s.tip + " " + s.tip2}>It’s a command </div>
      <div className={s.tip + " " + s.tip3}>
        The token looks like this<br />
        <strong>123456:ABC–DEF1234ghI–<br />zyx57W2v1u123ew11</strong>
      </div>
    </div>

    </div>
  );
};
