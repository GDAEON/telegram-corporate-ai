import React, { useRef, useState, useEffect } from "react";
import { Button, Input, InputRef, Space, Table, Tag, Popconfirm, message } from "antd";
import type {
  ColumnType,
  ColumnsType,
  TablePaginationConfig,
} from "antd/es/table";
import {
  CheckOutlined,
  CloseOutlined,
  DeleteOutlined,
  SearchOutlined,
  ShareAltOutlined,
} from "@ant-design/icons";
import Highlighter from "react-highlight-words";
import s from "./AdminPanel.module.css";
import { BACKEND_IP } from "../../shared";

type Props = {
  onExit: () => void;
  botInfo: {
    botId: number;
    botName: string;
    passUuid: string;
    webUrl: string;
  };
};

interface DataType {
  key: string;
  name: string;
  phone: string;
  status: boolean;
  isOwner: boolean;
}

type DataIndex = keyof DataType;

export const AdminPanel: React.FC<Props> = ({ onExit, botInfo }) => {
  const [searchText, setSearchText] = useState("");
  const [searchedColumn, setSearchedColumn] = useState<DataIndex | "">("");
  const searchInput = useRef<InputRef>(null);
  const [data, setData] = useState<DataType[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 5,
    total: 0,
  });
  const { botId, botName, passUuid, webUrl } = botInfo;
  const [inviteCopied, setInviteCopied] = useState(false);
  const inviteTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (inviteTimer.current) {
        clearTimeout(inviteTimer.current);
      }
    };
  }, []);

  const handleInviteUser = async () => {
    if (!botId || !botName || !passUuid) return;
    try {
      const link = `https://t.me/${botName}?start=${passUuid}`;
      await navigator.clipboard.writeText(link);
      message.success("Invite link copied");
      setInviteCopied(true);
      if (inviteTimer.current) {
        clearTimeout(inviteTimer.current);
      }
      inviteTimer.current = setTimeout(() => setInviteCopied(false), 1000);
    } catch (e) {
      message.error((e as Error).message);
    }
  };

  const handleOpenConstructor = async () => {
    if (!webUrl) return;
    try {
      window.open(webUrl, "_blank", "noopener,noreferrer");
    } catch (e) {
      message.error((e as Error).message);
    }
  };

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

  const fetchData = async (
    page: number,
    pageSize: number,
    status?: boolean
  ) => {
    if (!botId) return;
    setLoading(true);

    const params = new URLSearchParams();
    params.append("page", String(page));
    params.append("per_page", String(pageSize));
    if (searchText) params.append("search", searchText);
    if (status !== undefined) params.append("status", String(status));

    const res = await fetch(
      `${BACKEND_IP}/${botId}/users?${params.toString()}`
    );
    const json = await res.json();

    if (!res.ok) {
      console.error("Failed to fetch bot users:", json);
      setLoading(false);
      return;
    }

    const usersArray = Array.isArray(json.users) ? json.users : [];
    setData(
      usersArray.map((u: any) => ({
        key: String(u.id),
        name: `${u.name ?? ""} ${u.surname ?? ""}`.trim(),
        phone: u.phone ?? "",
        status: u.status,
        isOwner: u.isOwner,
      }))
    );

    setPagination({
      current: page,
      pageSize: pageSize, 
      total: json.total || 0,
    });
    setLoading(false);
  };

  const handleStatusToggle = async (userId: string, currentStatus: boolean) => {
    if (!botId) return;

    try {
      const res = await fetch(
        `${BACKEND_IP}/bot/${botId}/user/${userId}?new_status=${!currentStatus}`,
        {
          method: "PATCH",
        }
      );

      if (!res.ok) {
        const json = await res.json();
        message.error(json.detail ?? "Failed to update status");
        return;
      }

      setData((prev) =>
        prev.map((u) =>
          u.key === userId ? { ...u, status: !currentStatus } : u
        )
      );
      message.success("Status updated");
    } catch (e) {
      message.error((e as Error).message);
    }
  };

  const handleDelete = async (userId: string) => {
    if (!botId) return;

    try {
      const res = await fetch(
        `${BACKEND_IP}/bot/${botId}/user/${userId}`,
        { method: "DELETE" }
      );

      if (!res.ok) {
        const json = await res.json();
        message.error(json.detail ?? "Failed to delete user");
        return;
      }

      setData((prev) => prev.filter((u) => u.key !== userId));
      message.success("User deleted");
    } catch (e) {
      message.error((e as Error).message);
    }
  };

  useEffect(() => {
    fetchData(pagination.current || 1, pagination.pageSize || 10);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [botId, pagination.current, pagination.pageSize, searchText]);

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
      render: (_, record) => {
        const { status, isOwner, key } = record;
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
              onClick={() => handleStatusToggle(key, status)}
            >
              {text}
            </Button>
            <Popconfirm
              title="Delete this user?"
              onConfirm={() => handleDelete(key)}
              okText="Yes"
              cancelText="No"
            >
              <Button variant="solid" color="danger">
                Delete <DeleteOutlined />
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <div className={s.PanelWrapper}>
      <h1>Hello OwnerName!</h1>
      <Button block type="primary" size="large" style={{ height: 50 }} onClick={handleOpenConstructor}>
        Open Constructor
      </Button>
      <Button
        icon={inviteCopied ? <CheckOutlined /> : <ShareAltOutlined />}
        onClick={handleInviteUser}
        type={inviteCopied ? "primary" : "default"}
        style={{ transition: "background-color 0.3s" }}
      >
        {inviteCopied ? "Invitation Link Copied" : "Invite user"}
      </Button>
      <Button color="danger" variant="outlined" onClick={onExit}>Exit <CloseOutlined /></Button>
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{
          ...pagination,
          showSizeChanger: true, 
          pageSizeOptions: ["5", "10", "20", "50"],
        }}
        onChange={(pag, filters) => {
          const newPage = pag.current || 1;
          const newSize = pag.pageSize || pagination.pageSize!;
          const status = filters.status
            ? (filters.status[0] as boolean)
            : undefined;

          setPagination({ ...pagination, current: newPage, pageSize: newSize });
          fetchData(newPage, newSize, status);
        }}
      />
    </div>
  );
};
