import React, { useRef, useState } from "react";
import { Button, Input, InputRef, Space, Table, Tag } from "antd";
import type { ColumnType, ColumnsType } from "antd/es/table";
import {
  DeleteOutlined,
  SearchOutlined,
  ShareAltOutlined,
} from "@ant-design/icons";
import Highlighter from "react-highlight-words";
import s from "./AdminPanel.module.css";

interface DataType {
  key: string;
  name: string;
  phone: string;
  status: boolean;
  isOwner: boolean;
}

const data: DataType[] = [
  { key: "1", name: "John Brown", phone: "+71111111111", status: true, isOwner: true },
  { key: "2", name: "Jim Green", phone: "+71111111111", status: false, isOwner: false },
  { key: "3", name: "Joe Black", phone: "+71111111111", status: true, isOwner: false },
];

type DataIndex = keyof DataType;

export const AdminPanel: React.FC = () => {
  const [searchText, setSearchText] = useState("");
  const [searchedColumn, setSearchedColumn] = useState<DataIndex | "">("");
  const searchInput = useRef<InputRef>(null);

  const handleSearch = (
    selectedKeys: string[],
    confirm: () => void,
    dataIndex: DataIndex
  ) => {
    confirm();
    setSearchText(selectedKeys[0]);
    setSearchedColumn(dataIndex);
  };

  const handleReset = (clearFilters: () => void) => {
    clearFilters();
    setSearchText("");
  };

  const getColumnSearchProps = (
    dataIndex: DataIndex
  ): ColumnType<DataType> => ({
    filterDropdown: ({
      setSelectedKeys,
      selectedKeys,
      confirm,
      clearFilters,
      close,
    }) => (
      <div style={{ padding: 8 }} onKeyDown={(e) => e.stopPropagation()}>
        <Input
          ref={searchInput}
          placeholder={`Search ${dataIndex}`}
          value={selectedKeys[0]}
          onChange={(e) =>
            setSelectedKeys(e.target.value ? [e.target.value] : [])
          }
          onPressEnter={() =>
            handleSearch(selectedKeys as string[], confirm, dataIndex)
          }
          style={{ marginBottom: 8, display: "block" }}
        />
        <Space>
          <Button
            type="primary"
            icon={<SearchOutlined />}
            size="small"
            onClick={() =>
              handleSearch(selectedKeys as string[], confirm, dataIndex)
            }
          >
            Search
          </Button>
          <Button
            size="small"
            onClick={() => clearFilters && handleReset(clearFilters)}
          >
            Reset
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => {
              confirm({ closeDropdown: false });
              setSearchText((selectedKeys as string[])[0]);
              setSearchedColumn(dataIndex);
            }}
          >
            Filter
          </Button>
          <Button type="link" size="small" onClick={() => close()}>
            Close
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered) => (
      <SearchOutlined style={{ color: filtered ? "#1677ff" : undefined }} />
    ),
    onFilter: (value, record) =>
      record[dataIndex]
        .toString()
        .toLowerCase()
        .includes((value as string).toLowerCase()),
    filterDropdownProps: {
      onOpenChange: (open) => {
        if (open) setTimeout(() => searchInput.current?.select(), 100);
      },
    },
    render: (text) =>
      searchedColumn === dataIndex ? (
        <Highlighter
          highlightStyle={{ backgroundColor: "#ffc069", padding: 0 }}
          searchWords={[searchText]}
          autoEscape
          textToHighlight={text?.toString() || ""}
        />
      ) : (
        text
      ),
  });

  const columns: ColumnsType<DataType> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      ...getColumnSearchProps("name"),
    },
    {
      title: "Phone",
      dataIndex: "phone",
      key: "phone",
      ...getColumnSearchProps("phone"),
      render: (text) => {
        const cleaned = String(text).replace(/\D/g, "");
        const m = cleaned.match(/^(\d{1})(\d{3})(\d{3})(\d{2})(\d{2})$/);
        if (m) {
          const [, country, area, exch, sub1, sub2] = m;
          const formatted = `+${country} (${area}) ${exch}-${sub1}-${sub2}`;
          return <a href={`tel:+${cleaned}`}>{formatted}</a>;
        }
        return <a href={`tel:+${cleaned}`}>{text}</a>;
      },
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      align: "center",
      filters: [
        { text: "Active", value: true },
        { text: "Not Active", value: false },
      ],
      onFilter: (value, record) => record.status === value,
      render: (_, { status }) => (
        <Tag color={status ? "green" : "red"}>
          {status ? "Active" : "Not Active"}
        </Tag>
      ),
    },
    {
      title: "Actions",
      key: "actions",
      align: "center",
      render: (_, { status, isOwner }) => {
        if (isOwner) {
          return <p>You</p>;
        }
        const color = status ? "danger" : "green";
        const text = status ? "Deactivate" : "Activate";
        const variant = status ? "outlined" : "filled";
        return (
          <Space size="middle">
            <Button
              color={color}
              variant={variant}
              style={{ minWidth: 100, textAlign: "center" }}
            >
              {text}
            </Button>
            <Button variant="solid" color="danger">
              Delete <DeleteOutlined />
            </Button>
          </Space>
        );
      },
    },
  ];

  return (
    <div className={s.PanelWrapper}>
      <h1>Hello OwnerName!</h1>
      <Button block type="primary" size="large" style={{ height: 50 }}>
        Open Constructor
      </Button>
      <Button icon={<ShareAltOutlined />}>Invite user</Button>
      <Table columns={columns} dataSource={data} loading={false} />
    </div>
  );
};
