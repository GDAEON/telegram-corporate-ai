import React, { useRef, useState, useEffect } from "react";
import { Button, Input, InputRef, Space, Table, Tag } from "antd";
import type { ColumnType, ColumnsType, TablePaginationConfig } from "antd/es/table";
import {
  DeleteOutlined,
  SearchOutlined,
  ShareAltOutlined,
} from "@ant-design/icons";
import Highlighter from "react-highlight-words";
import { useSearchParams } from "react-router-dom";
import s from "./AdminPanel.module.css";

interface DataType {
  key: string;
  name: string;
  phone: string;
  status: boolean;
  isOwner: boolean;
}

type DataIndex = keyof DataType;

export const AdminPanel: React.FC = () => {
  const [searchText, setSearchText] = useState("");
  const [searchedColumn, setSearchedColumn] = useState<DataIndex | "">("");
  const searchInput = useRef<InputRef>(null);
  const [data, setData] = useState<DataType[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [searchParams] = useSearchParams();
  const botId = searchParams.get("botId");

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

  const fetchData = async (page: number, status?: boolean) => {
    if (!botId) return;
    setLoading(true);
    const params = new URLSearchParams();
    params.append("page", String(page));
    if (searchText) params.append("search", searchText);
    if (status !== undefined) params.append("status", String(status));
    const res = await fetch(`http://80.82.38.72:1080/api/${botId}/users?${params.toString()}`);
    const json = await res.json();
    setData(
      json.users.map((u: any) => ({
        key: String(u.id),
        name: `${u.name ?? ""} ${u.surname ?? ""}`.trim(),
        phone: u.phone ?? "",
        status: u.status,
        isOwner: u.isOwner,
      }))
    );
    setPagination({ current: page, pageSize: 10, total: json.total });
    setLoading(false);
  };

  useEffect(() => {
    fetchData(pagination.current || 1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [botId, pagination.current, searchText]);

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
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={pagination}
        onChange={(pag, filters) => {
          setPagination({ ...pagination, current: pag.current });
          const status = filters.status ? (filters.status[0] as boolean) : undefined;
          fetchData(pag.current || 1, status);
        }}
      />
    </div>
  );
};
