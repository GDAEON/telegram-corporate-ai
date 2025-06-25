# Telegram Corporate AI Integration

This repository contains a full-stack application for integrating **Telegram bots** with a corporate messaging service. It consists of a **FastAPI** backend and a **React** frontend. Infrastructure services such as PostgreSQL, Redis, Prometheus, Loki, and Grafana are orchestrated via **Docker Compose**.

---

## Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Backend Overview](#backend-overview)
- [Frontend Overview](#frontend-overview)
- [Development Scripts](#development-scripts)
- [API Gateway Usage](#api-gateway-usage)
- [License](#license)

---

## Architecture

```
telegram-corporate-ai/
├── backend/        # FastAPI application
├── frontend/       # React single-page application
├── docker-compose.yml
└── ...
```

### Services

- **backend** – FastAPI API server
- **frontend** – React development server
- **postgres** – PostgreSQL database
- **redis** – Redis for caching
- **prometheus** – Metric collection service
- **grafana** – Visualization dashboard
- **loki** – Log aggregation service

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/)
- Optional: `node` and `npm` for running the frontend outside Docker

---

## Quick Start

1. Create a `.env` file in the root directory and define the environment variables (see below).
2. Start the services:

```bash
docker-compose up --build
```

3. Access the application:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Prometheus: [http://localhost:9090](http://localhost:9090)
   - Grafana: [http://localhost:3001](http://localhost:3001)
   - Loki: [http://localhost:3100](http://localhost:3100)

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `REACT_APP_BACKEND_IP` | Base API URL used by React |
| `WEBHOOK_URL` | Telegram webhook URL |
| `INTEGRATION_URL` | Corporate service URL |
| `INTEGRATION_CODE` | Integration code |
| `INTEGRATION_TOKEN` | Bearer token for API access |
| `POSTGRES_URL` | PostgreSQL hostname |
| `POSTGRES_USER` | PostgreSQL user |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | PostgreSQL DB name |
| `FERNET_KEY` | Key for encrypting sensitive fields |
| `REDIS_URL` | Redis hostname |
| `REDIS_PASSWORD` | Redis password |
| `REDIS_CACHE_TIME` | TTL for Redis cache (in seconds) |
| `PROMETHEUS_JOBS_PATH` | Path to Prometheus jobs config file |
| `LOKI_URL` | URL for Loki log ingestion |

---

## Backend Overview

Located in the `backend/` directory. The main features:

### Telegram Webhook
- `POST /webhook/{bot_id}` – Handles Telegram updates and forwards to the corporate service.

### Constructor API
- `GET /schema`
- `GET /messengers`
- `POST /sendTextMessage`
- `POST /sendMediaMessage`

### Integration API (`/api` prefix)
- Register and manage bots and their owners
- Manage bot users
- Generate invite tokens, refresh URLs, verify statuses

### Metrics API
- `GET /metrics`
- `GET /metrics/jobs`
- `POST /metrics/job`
- `DELETE /metrics/job/{name}`

### Data Persistence
- PostgreSQL models: `backend/constants/postgres_models.py`
- Redis models: `backend/constants/redis_models.py`
- Prometheus metrics: `backend/constants/prometheus_models.py`
- Logs: `logs/interactions.log`
- Logs forwarded to Loki

---

## Frontend Overview

Located in the `frontend/` directory. Main React pages/components:

- **ConnectionPage** – Connect or select bots
- **ConnectionForm** – Input Telegram bot token
- **OwnerQRModal** – QR code for verifying ownership
- **AdminPanel** – User management, messaging, and invitations

Supports i18n with `react-i18next` (English and Russian). Backend URL comes from `REACT_APP_BACKEND_IP`.

---

## Development Scripts

Each service has its own helpers:

### Backend
```bash
./backend/run.sh  # Launch with Uvicorn
pytest            # Run backend tests
```

### Frontend
```bash
npm start         # Run development server
npm run build     # Build production version
npm test          # Run tests
```

---

## API Gateway Usage

This project is compatible with **Yandex Cloud API Gateway**. Below is a simplified example of the OpenAPI configuration:

```yaml
openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
x-yc-apigateway:
  variables:
    service_url:
      default: 5b59-166-1-157-129.ngrok-free.app
      description: ngrok or backend base URL
    frontend_url:
      default: 5b59-166-1-157-129.ngrok-free.app
      description: ngrok or frontend base URL
servers:
- url: https://d5d1dfaumqfvtppjsai1.ubofext2.apigw.yandexcloud.net
paths:
  /{proxy+}:
    get:
      summary: Serve React SPA
      parameters:
        - name: proxy
          in: path
          required: true
          schema:
            type: string
      x-yc-apigateway-integration:
        type: http
        method: GET
        url: http://${var.frontend_url}/{proxy}
        headers:
          Host: ${var.frontend_url}
      responses:
        '200':
          description: OK

  /:
    get:
      summary: Serve React root
      x-yc-apigateway-integration:
        type: http
        method: GET
        url: http://${var.frontend_url}/
        headers:
          Host: ${var.frontend_url}
      responses:
        '200':
          description: OK
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /docs:
    get:
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
        method: get
        type: http
        url: http://${var.service_url}/docs
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /openapi.json:
    get:
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
        method: get
        type: http
        url: http://${var.service_url}/openapi.json
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /webhook/{bot_id}:
    post:
      summary: Webhook for specific bot
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        type: http
        method: post
        url: http://${var.service_url}/webhook/{bot_id}
        headers:
          Host: ${var.service_url}
          '*': '*'
        query:
          '*': '*'
      responses:
        '200':
          description: OK
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: string
  /bot:
    post:
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: post
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/bot
    delete:
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: delete
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/bot
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /schema:
    get:
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/schema
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /extraVariables:
    get:
      x-yc-apigateway-integration:
        http_code: 200
        type: dummy
        content:
          application/json: '[]'
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /messengers:
    get:
      x-yc-apigateway-integration:
        headers:
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/messengers
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /sendTextMessage:
    post:
      x-yc-apigateway-integration:
        headers:
          '*': '*'
        method: post
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/sendTextMessage
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /sendMediaMessage:
    post:
      x-yc-apigateway-integration:
        headers:
          '*': '*'
        method: post
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/sendMediaMessage
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /api/bot:
    post:
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: post
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/bot
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /api/owner/{owner_uuid}/bots:
    get:
      parameters:
      - name: owner_uuid
        in: path
        required: true
        schema:
          type: string
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/owner/{owner_uuid}/bots
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: owner_uuid
        in: path
        required: true
        schema:
          type: string
  /api/{bot_id}/isVerified:
    get:
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/{bot_id}/isVerified
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: string
  /api/{bot_id}/users:
    get:
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/{bot_id}/users
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: string
  /api/{bot_id}/owner:
    get:
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/{bot_id}/owner
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: string
  /api/{bot_id}/authInfo:
    get:
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/{bot_id}/authInfo
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: string
  /api/bot/{bot_id}/refresh:
    post:
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: post
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/bot/{bot_id}/refresh
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: string
  /api/bot/{bot_id}/logout:
    patch:
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: patch
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/bot/{bot_id}/logout
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: string
  /api/bot/{bot_id}/invite:
    post:
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: post
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/bot/{bot_id}/invite
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: string
  /api/bot/{bot_id}/user/{user_id}:
    patch:
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      - name: user_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: patch
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/bot/{bot_id}/user/{user_id}
    delete:
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: integer
      - name: user_id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: delete
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/api/bot/{bot_id}/user/{user_id}
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: bot_id
        in: path
        required: true
        schema:
          type: string
      - name: user_id
        in: path
        required: true
        schema:
          type: string
  /metrics/:
    get:
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/metrics/
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /metrics/jobs:
    get:
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/metrics/jobs
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /metrics/job:
    post:
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: post
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/metrics/job
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
  /metrics/job/{name}:
    delete:
      parameters:
      - name: name
        in: path
        required: true
        schema:
          type: string
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: delete
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/metrics/job/{name}
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: name
        in: path
        required: true
        schema:
          type: string
  /{id}/status:
    get:
      parameters:
      - name: id
        in: path
        required: true
        schema:
          type: integer
      x-yc-apigateway-integration:
        headers:
          Host: ${var.service_url}
          '*': '*'
        method: get
        query:
          '*': '*'
        type: http
        url: http://${var.service_url}/{id}/status
    options:
      x-yc-apigateway-integration:
        type: dummy
        http_code: 204
        content:
          application/json: ''
        http_headers:
          Access-Control-Allow-Origin: '*'
          Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
          Access-Control-Allow-Headers: '*'
          Access-Control-Max-Age: '3600'
      parameters:
      - name: id
        in: path
        required: true
        schema:
          type: string

```

> **Note**: Full CORS support is included via `options` dummy integrations.

---

## License

Distributed under the [MIT License](LICENSE).

---

For detailed API Gateway configuration, refer to `api-gateway.yaml` inside the project.
