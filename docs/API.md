# 旅行计划 API 接口文档

> **Base URL:** `http://localhost:8000`
> **API 版本:** v0.1.0
> **接口前缀:** `/api/v1`

---

## 目录

- [通用说明](#通用说明)
- [健康检查](#健康检查)
- [认证模块](#认证模块)
  - [1. 发送邮箱验证码](#1-发送邮箱验证码)
  - [2. 邮箱注册](#2-邮箱注册)
  - [3. 密码登录](#3-密码登录)
  - [4. 重置密码](#4-重置密码)
  - [5. 获取当前用户信息](#5-获取当前用户信息)
- [足迹模块](#足迹模块)
  - [1. 逆地理编码](#1-逆地理编码)
  - [2. 创建足迹](#2-创建足迹)
  - [3. 足迹详情](#3-足迹详情)
  - [4. 更新足迹](#4-更新足迹)
  - [5. 删除足迹](#5-删除足迹)
  - [6. 上传足迹图片](#6-上传足迹图片)
  - [7. 按旅程列出足迹](#7-按旅程列出足迹)
  - [8. 批量排序足迹](#8-批量排序足迹)
- [公共数据结构](#公共数据结构)
- [错误码说明](#错误码说明)

---

## 通用说明

### 鉴权方式

需要登录的接口在请求头中携带 JWT：

```
Authorization: Bearer <access_token>
```

### 响应格式

所有接口返回 JSON。成功时直接返回业务数据，失败时返回：

```json
{
  "detail": "错误描述信息"
}
```

### 验证码规则

| 规则 | 值 |
|------|----|
| 验证码长度 | 6 位纯数字 |
| 有效期 | 5 分钟 |
| 同一邮箱最短发送间隔 | 60 秒 |
| 验证成功后 | 立即失效（一次性） |

---

## 健康检查

### `GET /health`

服务健康检查，用于部署监控。

**请求参数：** 无

**响应示例：**

```json
{
  "status": "ok"
}
```

---

## 认证模块

### 1. 发送邮箱验证码

#### `POST /api/v1/auth/send-code`

向指定邮箱发送 6 位数字验证码，用于注册或重置密码。

**是否需要登录：** 否

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址（需符合邮箱格式） |

**请求示例：**

```json
{
  "email": "user@example.com"
}
```

**成功响应：** `200 OK`

```json
{
  "message": "验证码已发送，请查收邮箱"
}
```

**错误响应：**

| HTTP 状态码 | detail | 触发条件 |
|-------------|--------|----------|
| 422 | 请求校验失败 | 邮箱格式不正确 |
| 429 | 发送过于频繁，请稍后再试 | 60 秒内重复请求 |
| 500 | 验证码发送失败，请稍后重试 | SMTP 发送异常 |

---

### 2. 邮箱注册

#### `POST /api/v1/auth/register`

使用邮箱 + 验证码完成注册，注册成功后直接返回登录态（JWT）。

**是否需要登录：** 否

**前置条件：** 先调用 [发送邮箱验证码](#1-发送邮箱验证码) 获取验证码

**请求体：**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| email | string | 是 | 邮箱格式 | 注册邮箱 |
| code | string | 是 | 固定 6 位 | 邮箱验证码 |
| password | string | 是 | 6 ~ 64 字符 | 登录密码 |
| nickname | string | 否 | 最长 50 字符 | 昵称，不填则默认取邮箱前缀 |

**请求示例：**

```json
{
  "email": "user@example.com",
  "code": "382916",
  "password": "mypassword123",
  "nickname": "旅行者"
}
```

**成功响应：** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nickname": "旅行者",
    "avatar": "",
    "email": "user@example.com",
    "bio": "",
    "is_active": true,
    "email_verified": true,
    "last_login_at": null,
    "created_at": "2026-02-28T10:30:00",
    "updated_at": "2026-02-28T10:30:00"
  }
}
```

**错误响应：**

| HTTP 状态码 | detail | 触发条件 |
|-------------|--------|----------|
| 400 | 验证码已过期或未发送 | 验证码超过 5 分钟 / 未发送 |
| 400 | 验证码错误 | 验证码不匹配 |
| 400 | 该邮箱已注册 | 邮箱已存在 |
| 422 | 请求校验失败 | 字段格式/长度不满足约束 |

---

### 3. 密码登录

#### `POST /api/v1/auth/login`

使用邮箱 + 密码登录，返回 JWT 和用户信息。

**是否需要登录：** 否

**请求体：**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| email | string | 是 | 邮箱格式 | 登录邮箱 |
| password | string | 是 | 6 ~ 64 字符 | 登录密码 |

**请求示例：**

```json
{
  "email": "user@example.com",
  "password": "mypassword123"
}
```

**成功响应：** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nickname": "旅行者",
    "avatar": "",
    "email": "user@example.com",
    "bio": "",
    "is_active": true,
    "email_verified": true,
    "last_login_at": "2026-02-28T10:35:00",
    "created_at": "2026-02-28T10:30:00",
    "updated_at": "2026-02-28T10:35:00"
  }
}
```

**错误响应：**

| HTTP 状态码 | detail | 触发条件 |
|-------------|--------|----------|
| 401 | 邮箱或密码错误 | 邮箱不存在 / 密码不正确 |
| 401 | 该账号已被禁用 | `is_active = false` |
| 422 | 请求校验失败 | 字段格式/长度不满足约束 |

---

### 4. 重置密码

#### `POST /api/v1/auth/reset-password`

通过邮箱验证码重置密码。

**是否需要登录：** 否

**前置条件：** 先调用 [发送邮箱验证码](#1-发送邮箱验证码) 获取验证码

**请求体：**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| email | string | 是 | 邮箱格式 | 注册邮箱 |
| code | string | 是 | 固定 6 位 | 邮箱验证码 |
| new_password | string | 是 | 6 ~ 64 字符 | 新密码 |

**请求示例：**

```json
{
  "email": "user@example.com",
  "code": "582047",
  "new_password": "newpassword456"
}
```

**成功响应：** `200 OK`

```json
{
  "message": "密码重置成功，请使用新密码登录"
}
```

**错误响应：**

| HTTP 状态码 | detail | 触发条件 |
|-------------|--------|----------|
| 400 | 验证码已过期或未发送 | 验证码超过 5 分钟 / 未发送 |
| 400 | 验证码错误 | 验证码不匹配 |
| 400 | 该邮箱尚未注册 | 邮箱不存在 |
| 422 | 请求校验失败 | 字段格式/长度不满足约束 |

---

### 5. 获取当前用户信息

#### `GET /api/v1/auth/me`

获取当前已登录用户的详细信息。

**是否需要登录：** 是

**请求头：**

```
Authorization: Bearer <access_token>
```

**请求参数：** 无

**成功响应：** `200 OK`

```json
{
  "id": 1,
  "nickname": "旅行者",
  "avatar": "https://cdn.yourdomain.com/avatars/1.jpg",
  "email": "user@example.com",
  "bio": "热爱旅行的人",
  "is_active": true,
  "email_verified": true,
  "last_login_at": "2026-02-28T10:35:00",
  "created_at": "2026-02-28T10:30:00",
  "updated_at": "2026-02-28T10:35:00"
}
```

**错误响应：**

| HTTP 状态码 | detail | 触发条件 |
|-------------|--------|----------|
| 401 | 未提供认证令牌 | 请求头缺少 Authorization |
| 401 | 令牌无效或已过期 | JWT 解析失败 / 已过期 |
| 401 | 用户不存在 | token 中的用户已被删除 |
| 403 | 账号已被禁用 | `is_active = false` |

---

## 足迹模块

### 1. 逆地理编码

#### `GET /api/v1/geocode/reverse`

根据经纬度获取地址信息（高德 Web 服务）。需在环境变量中配置 `AMAP_WEB_SERVICE_KEY`。

**是否需要登录：** 是

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| lat | number | 是 | 纬度 [-90, 90] |
| lng | number | 是 | 经度 [-180, 180] |

**成功响应：** `200 OK`

```json
{
  "location_name": "北京大学",
  "address": "北京市海淀区颐和园路5号",
  "district": "海淀区",
  "city_name": "北京市",
  "province_name": "北京市",
  "country_name": "中国"
}
```

未配置 Key 或请求失败时返回空字符串字段。

---

### 2. 创建足迹

#### `POST /api/v1/footprints`

创建一条足迹。经纬度必填；`travel_id` 可选，不传则自动归属当前「进行中」的旅程。若未传地址信息，服务端会尝试逆地理编码填充。

**是否需要登录：** 是

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| latitude | number | 是 | 纬度 |
| longitude | number | 是 | 经度 |
| travel_id | integer \| null | 否 | 所属旅程 ID，不传则自动归属进行中的旅程 |
| description | string \| null | 否 | 足迹描述 |
| travel_time | string \| null | 否 | 到达时间（ISO 8601，用于路线串联） |
| location_name | string | 否 | 地点名称（逆地理或手动） |
| address | string | 否 | 详细地址 |
| district | string | 否 | 区县 |
| city_name | string | 否 | 城市 |
| province_name | string | 否 | 省份 |
| country_name | string | 否 | 国家 |

**成功响应：** `201 Created`，返回足迹对象（含 `id`、`travel_id`、经纬度、地址字段、`cover_thumbnail_url`、`image_count`、`sort_order`、`created_at` 等）。

**错误响应：** 未指定旅程且没有进行中的旅程时返回 400。

---

### 3. 足迹详情

#### `GET /api/v1/footprints/{footprint_id}`

获取单条足迹详情（含图片列表）。公开旅程的足迹可被他人查看。

**是否需要登录：** 可选（未登录只能看公开旅程的足迹）

**成功响应：** `200 OK`，包含 `images` 数组（每项含 `original_url`、`thumbnail_url`、`sort_order` 等）。

---

### 4. 更新足迹

#### `PUT /api/v1/footprints/{footprint_id}`

更新足迹（支持手动调整位置、描述、到达时间、排序等）。若修改了经纬度或地址相关字段，`location_adjusted` 会自动设为 `true`。

**是否需要登录：** 是

**请求体：** 所有字段可选。可包含 `latitude`、`longitude`、`location_name`、`address`、`district`、`city_name`、`province_name`、`country_name`、`location_adjusted`、`description`、`travel_time`、`sort_order`。

---

### 5. 删除足迹

#### `DELETE /api/v1/footprints/{footprint_id}`

删除足迹及其全部图片（OSS 上的原图与缩略图一并删除），并更新所属旅程的足迹数、图片数。

**是否需要登录：** 是

**成功响应：** `200 OK`，`{ "message": "足迹已删除" }`。

---

### 6. 上传足迹图片

#### `POST /api/v1/footprints/{footprint_id}/images`

上传一张图片：原图与缩略图（400×400）上传至 OSS，首图将作为该足迹的封面（`cover_thumbnail_url`）。

**是否需要登录：** 是

**请求体：** `multipart/form-data`，字段 `file` 为图片文件（支持 jpeg/png/webp，单张不超过 10 MB）。

**成功响应：** `201 Created`，返回图片对象（`id`、`original_url`、`thumbnail_url`、`sort_order` 等）。

---

### 7. 按旅程列出足迹

#### `GET /api/v1/travels/{travel_id}/footprints`

分页列出某旅程下的足迹。排序方式：`order_by=default` 按 `sort_order`、`travel_time`、`id`；`order_by=travel_time` 按到达时间、id。用于地图展示与路线串联。

**是否需要登录：** 可选（私密旅程需本人）

**Query 参数：** `page`、`page_size`、`order_by`（default \| travel_time）。

**成功响应：** `200 OK`，`{ "items": [...], "total": n, "page": 1, "page_size": 50 }`。

---

### 8. 批量排序足迹

#### `PUT /api/v1/travels/{travel_id}/footprints/reorder`

可拖动排序：按 `footprint_id` + `sort_order` 批量更新该旅程下足迹的排序。

**是否需要登录：** 是

**请求体：**

```json
{
  "items": [
    { "footprint_id": 1, "sort_order": 0 },
    { "footprint_id": 2, "sort_order": 1 }
  ]
}
```

**成功响应：** `200 OK`，`{ "message": "排序已更新" }`。

---

## 公共数据结构

### UserInfo

用户信息对象，多个接口共用。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户 ID |
| nickname | string | 昵称 |
| avatar | string | 头像 URL（未设置时为空字符串） |
| email | string | 邮箱 |
| bio | string | 个人简介（未设置时为空字符串） |
| is_active | boolean | 账号是否启用 |
| email_verified | boolean | 邮箱是否已验证 |
| last_login_at | string \| null | 最后登录时间（ISO 8601），未登录过为 null |
| created_at | string | 创建时间（ISO 8601） |
| updated_at | string | 更新时间（ISO 8601） |

### TokenResponse

登录/注册成功后返回的令牌对象。

| 字段 | 类型 | 说明 |
|------|------|------|
| access_token | string | JWT 令牌 |
| token_type | string | 固定值 `"bearer"` |
| user | UserInfo | 用户信息 |

### MessageResponse

操作结果消息。

| 字段 | 类型 | 说明 |
|------|------|------|
| message | string | 结果描述 |

---

## 错误码说明

| HTTP 状态码 | 含义 | 常见场景 |
|-------------|------|----------|
| 200 | 成功 | 请求正常处理 |
| 400 | 请求错误 | 验证码错误、邮箱已注册等业务校验失败 |
| 401 | 未授权 | 未登录、token 过期、密码错误 |
| 403 | 禁止访问 | 账号被禁用 |
| 422 | 参数校验失败 | 字段缺失、格式不正确、长度不满足约束 |
| 429 | 请求过于频繁 | 验证码发送间隔不足 60 秒 |
| 500 | 服务器内部错误 | 邮件发送失败等服务异常 |

---

## 业务流程

### 注册流程

```
客户端                          服务端                        Redis              邮箱
  │                               │                            │                  │
  │  POST /auth/send-code         │                            │                  │
  │──────────────────────────────►│                            │                  │
  │                               │  检查 60s 频率限制          │                  │
  │                               │───────────────────────────►│                  │
  │                               │  生成 6 位验证码            │                  │
  │                               │  存储验证码 (TTL=300s)      │                  │
  │                               │───────────────────────────►│                  │
  │                               │  存储频率限制 (TTL=60s)     │                  │
  │                               │───────────────────────────►│                  │
  │                               │  发送验证码邮件             │                  │
  │                               │───────────────────────────────────────────────►│
  │  { message: "验证码已发送" }   │                            │                  │
  │◄──────────────────────────────│                            │                  │
  │                               │                            │                  │
  │  POST /auth/register          │                            │                  │
  │──────────────────────────────►│                            │                  │
  │                               │  从 Redis 取验证码并比对    │                  │
  │                               │───────────────────────────►│                  │
  │                               │  校验通过 → 删除验证码      │                  │
  │                               │  检查邮箱是否已注册 (MySQL) │                  │
  │                               │  创建用户 → 签发 JWT        │                  │
  │  { access_token, user }       │                            │                  │
  │◄──────────────────────────────│                            │                  │
```

### 登录流程

```
客户端                          服务端                        MySQL
  │                               │                            │
  │  POST /auth/login             │                            │
  │──────────────────────────────►│                            │
  │                               │  查询用户 by email          │
  │                               │───────────────────────────►│
  │                               │  bcrypt 验证密码            │
  │                               │  更新 last_login_at         │
  │                               │───────────────────────────►│
  │                               │  签发 JWT                   │
  │  { access_token, user }       │                            │
  │◄──────────────────────────────│                            │
```

---

> **OpenAPI 规范（供前端/工具直接使用）：**
> - 静态文件：`docs/openapi.json`
> - 运行时：`GET http://localhost:8000/openapi.json`
> - 前端对接说明：见 [API-前端使用说明.md](./API-前端使用说明.md)
>
> **Swagger UI：** 启动服务后访问 `http://localhost:8000/docs`
>
> **ReDoc：** 启动服务后访问 `http://localhost:8000/redoc`
