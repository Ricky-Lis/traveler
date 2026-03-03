# 前端对接 API 说明

本文说明如何用**机器可读**的 API 文档对接前端，便于生成类型、客户端或联调。

## 1. OpenAPI 文档位置

| 来源 | 地址/路径 | 说明 |
|------|-----------|------|
| 静态文件（推荐用于代码生成） | `docs/openapi.json` | 项目内 OpenAPI 3.0 规范，不依赖服务运行 |
| 运行时动态（与代码一致） | `GET http://localhost:8000/openapi.json` | 需先启动后端，返回与当前代码一致的规范 |

前端可任选其一：本地开发用静态文件即可；若后端经常改接口，可从运行中的服务拉取最新规范。

## 2. 鉴权

需要登录的接口在请求头携带 JWT：

```http
Authorization: Bearer <access_token>
```

`<access_token>` 来自 **登录** 或 **注册** 接口返回的 `access_token` 字段。

## 3. 前端常见用法

### 3.1 导入 Postman / Apifox / Insomnia

- 打开工具 → 导入 (Import) → 选择 `docs/openapi.json` 或填入 `http://localhost:8000/openapi.json`
- 可为需要登录的接口在环境变量中配置 `Authorization: Bearer {{access_token}}`

### 3.2 生成 TypeScript/JavaScript 请求客户端

使用 [OpenAPI Generator](https://openapi-generator.tech/) 或 [openapi-typescript-codegen](https://github.com/ferdikoomen/openapi-typescript-codegen)：

```bash
# 示例：openapi-generator-cli 生成 TS axios 客户端
npx @openapi-generators/cli -i docs/openapi.json -o src/api -g typescript-axios

# 或使用 openapi-typescript-codegen（先安装）
npx openapi --input docs/openapi.json --output ./src/api --client axios
```

生成后可直接在项目里调用封装好的接口函数，并带类型提示。

### 3.3 仅生成 TypeScript 类型

若只需请求/响应的类型定义：

```bash
npx openapi-typescript docs/openapi.json -o src/api/schema.d.ts
```

### 3.4 Swagger UI / ReDoc（人读文档）

- 本地启动后端后访问：
  - **Swagger UI：** http://localhost:8000/docs  
  - **ReDoc：** http://localhost:8000/redoc  
- 两者均基于同一份 OpenAPI 规范，可直接在页面上试调接口。

## 4. 错误响应格式

接口失败时通常返回：

```json
{ "detail": "错误描述信息" }
```

`detail` 可能是字符串，也可能是校验错误数组（如 422 时）。HTTP 状态码见 API 文档中的「错误码说明」。

## 5. 更新 OpenAPI 文档

- 若后端使用 FastAPI 且路由/模型有改动，可重新导出规范：
  ```bash
  python scripts/export_openapi.py
  ```
  会覆盖 `docs/openapi.json`。
- 或直接使用运行时的 `GET /openapi.json` 获取最新规范。

---

**相关文档：** [API.md](./API.md) — 人工阅读的接口说明与示例。
