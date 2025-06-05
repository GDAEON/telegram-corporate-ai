import React from "react";
import type { FormProps } from "antd";
import { Button, Form, Input, Typography } from "antd";
import s from "./ConnectionForm.module.css";

const { Title, Text } = Typography;

type FieldType = {
  token?: string;
};

const onFinish: FormProps<FieldType>["onFinish"] = (values) => {
  console.log("Success:", values);
};

const onFinishFailed: FormProps<FieldType>["onFinishFailed"] = (errorInfo) => {
  console.log("Failed:", errorInfo);
};

export const ConnectionFormView: React.FC = () => {
  return (
    <div>
      <h1 className={s.FormTitle}>Connect Telegram Bot</h1>
      <Form
        style={{ width: 450 }}
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
          <Input placeholder="Paste your bot token here..." />
        </Form.Item>

        <Form.Item>
          <Button block type="primary" size="large" htmlType="submit">
            Connect
          </Button>
        </Form.Item>
      </Form>

      <div className={s.instructions}>
        <Title level={4}>How to obtain a bot token:</Title>
        <div className={s.stepRow}>
          <div className={s.stepText}>
            <Text>
              <Text strong>1.</Text> On Telegram, open a chat with the
              <Text code>BotFather</Text>.
            </Text>
          </div>
          <div className={s.callout}>
            <Text>Search for “BotFather”</Text>
          </div>
        </div>

        <div className={s.stepRow}>
          <div className={s.stepText}>
            <Text>
              <Text strong>2.</Text> Send the <Text code>/newbot</Text> command
              and follow the instructions.
            </Text>
          </div>
          <div className={s.callout}>
            <Text>It’s a command</Text>
          </div>
        </div>

        <div className={s.stepRow}>
          <div className={s.stepText}>
            <Text>
              <Text strong>3.</Text> Copy the token shown in the response.
            </Text>
          </div>
          <div className={s.callout}>
            <Text>
              The token looks like this
              <br />
              <Text code>123456:ABC-DEF1234ghI-zyx57W2v1u123ew11</Text>
            </Text>
          </div>
        </div>
      </div>
    </div>
  );
};
