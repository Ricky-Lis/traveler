# traveler

旅行地图 Web 应用示例，面向旅行爱好者。通过 AI 辅助全流程开发，集成地图与个性化行程能力。

## 配置与安全

- **配置来源**：所有敏感配置（数据库密码、JWT 密钥、SMTP、OSS、高德 Key 等）均通过 **环境变量** 或 **`.env` 文件** 读取，代码中不包含任何默认密钥。
- **本地/部署**：复制 `.env.example` 为 `.env`，按需填写后运行应用；`.env` 已被 `.gitignore` 排除，不会进入版本库。
  - Windows: `copy .env.example .env`
  - Linux/Mac: `cp .env.example .env`

## 推送到 GitHub 公开仓库

1. **确认未提交敏感文件**
   - 根目录已有 `.gitignore`，会排除：`.env`、`__pycache__/`、`.idea/`、`*.log`、`export_log.txt` 等。
   - 确保从未执行过 `git add .env` 或 `git add app/config.py` 在清理之前的版本；若曾提交过 `.env` 或带密钥的 `config.py`，需用 `git filter-branch` 或 BFG 从历史中移除后再推送。

2. **推送前自检（可选）**
   ```bash
   # 查看将被提交的文件，确认没有 .env、.idea、__pycache__
   git status
   git add .
   git status
   ```
   若列表中出现 `.env` 或 `.idea`，说明未被忽略，请检查 `.gitignore` 是否在仓库根目录且已保存。

3. **首次推送**
   ```bash
   git remote add origin https://github.com/你的用户名/traveler.git
   git add .
   git commit -m "Initial commit: travel app with env-based config"
   git push -u origin main
   ```
   若默认分支是 `master`，将上面命令中的 `main` 改为 `master`。

4. **克隆者使用方式**
   - 克隆后复制 `.env.example` 为 `.env`，填写自己的数据库、Redis、JWT 密钥等即可本地运行。
