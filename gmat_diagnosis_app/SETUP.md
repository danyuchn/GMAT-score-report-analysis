# GMAT 診斷應用環境設置指南

## 環境變量設置

從 2024 年版本開始，GMAT 診斷應用採用更安全的 API 金鑰管理方式。需要設置以下環境變量：

1. `OPENAI_API_KEY`：您的 OpenAI API 金鑰，用於後端調用 OpenAI API 服務。
2. `MASTER_KEY`：自定義的管理金鑰，用戶需要在前端輸入此金鑰以使用 AI 功能。

您可以通過以下方式設置環境變量：

### 本地開發環境

創建一個 `.env` 文件在專案根目錄，內容如下：

```
OPENAI_API_KEY=sk-your_actual_openai_api_key_here
MASTER_KEY=your_custom_master_key_here
```

### 部署環境

在服務器或容器平台上，使用平台提供的環境變量設置功能：

```bash
# Linux/macOS
export OPENAI_API_KEY=sk-your_actual_openai_api_key_here
export MASTER_KEY=your_custom_master_key_here

# Windows CMD
set OPENAI_API_KEY=sk-your_actual_openai_api_key_here
set MASTER_KEY=your_custom_master_key_here

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-your_actual_openai_api_key_here"
$env:MASTER_KEY = "your_custom_master_key_here"
```

### Docker 部署

如果使用 Docker 部署，可以在 `docker-compose.yml` 文件中設置環境變量：

```yaml
version: '3'
services:
  gmat-app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=sk-your_actual_openai_api_key_here
      - MASTER_KEY=your_custom_master_key_here
```

或使用 `.env` 文件搭配 Docker Compose：

```yaml
version: '3'
services:
  gmat-app:
    build: .
    ports:
      - "8501:8501"
    env_file:
      - .env
```

## 安全性說明

- 注意：`.env` 文件不應提交到版本控制系統（git），應該添加到 `.gitignore` 中。
- 請確保 `MASTER_KEY` 足夠複雜且難以猜測，以保證系統安全。
- 使用此方式可避免將 API 金鑰暴露給最終用戶，提高應用的安全性。
- 每當應用重新啟動時，環境變量需要重新設置，除非您使用了永久性的環境變量設置方法。

## 使用說明

1. 設置環境變量後，重啟應用程序。
2. 用戶需要在應用界面的側邊欄輸入 `MASTER_KEY` 以啟用 AI 功能。
3. 後端會使用環境變量中的 `OPENAI_API_KEY` 進行 API 調用，無需用戶輸入實際的 API 密鑰。

這種方式比讓用戶直接在前端輸入 API 密鑰更安全，因為：
1. 實際的 API 密鑰不會在前端顯示或傳輸
2. 可以控制誰可以使用 API 服務
3. 減少了 API 密鑰洩露的風險
4. 符合安全最佳實踐 