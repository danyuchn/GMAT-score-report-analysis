# SSH 金鑰設置指南

## 概述
本指南將協助您設置 SSH 金鑰認證並禁用 VPS 上的密碼登入，以提高安全性。

## 已完成的步驟
✅ **步驟 1：生成新的 SSH 金鑰對**
- 金鑰類型：ED25519
- 私鑰：`~/.ssh/id_ed25519_vps`
- 公鑰：`~/.ssh/id_ed25519_vps.pub`

## 接下來的步驟

### 步驟 2：將公鑰複製到 VPS
執行以下命令將公鑰複製到您的 VPS：

```bash
./setup_ssh_vps.sh <username> <vps_ip_or_domain>
```

**範例：**
```bash
# 如果您的 VPS 使用 root 使用者
./setup_ssh_vps.sh root 192.168.1.100

# 如果您的 VPS 使用其他使用者名稱
./setup_ssh_vps.sh ubuntu example.com
```

這個腳本會：
- 驗證 SSH 金鑰存在
- 測試與伺服器的連線
- 複製公鑰到伺服器
- 測試金鑰登入是否正常

### 步驟 3：禁用密碼認證
在確認金鑰登入正常後，執行以下命令禁用密碼認證：

```bash
./disable_password_auth.sh <username> <vps_ip_or_domain>
```

**範例：**
```bash
./disable_password_auth.sh root 192.168.1.100
```

⚠️ **重要警告：** 此操作會禁用密碼登入。請確保金鑰認證正常工作，否則可能被鎖定在伺服器外！

## 連線到 VPS

### 方法 1：直接使用金鑰檔案
```bash
ssh -i ~/.ssh/id_ed25519_vps username@vps_host
```

### 方法 2：使用 SSH 配置檔案（推薦）
1. 編輯 SSH 配置檔案：
   ```bash
   nano ~/.ssh/config
   ```

2. 添加配置（參考 `ssh_config_template` 檔案）：
   ```
   Host vps
       HostName YOUR_VPS_IP
       User YOUR_USERNAME
       IdentityFile ~/.ssh/id_ed25519_vps
       PasswordAuthentication no
   ```

3. 使用別名連線：
   ```bash
   ssh vps
   ```

## 檔案說明

| 檔案名稱 | 用途 |
|---------|------|
| `setup_ssh_vps.sh` | 將公鑰複製到 VPS 並設置金鑰認證 |
| `disable_password_auth.sh` | 禁用 VPS 上的密碼認證 |
| `ssh_config_template` | SSH 配置檔案模板 |
| `SSH_SETUP_GUIDE.md` | 本使用指南 |

## 安全提示

### ✅ 良好的安全實踐
- 定期備份您的私鑰檔案
- 為私鑰設置密碼保護
- 不要將私鑰檔案分享給他人
- 定期更新 SSH 金鑰

### 🔒 伺服器安全配置
腳本會自動設置以下安全配置：
- `PasswordAuthentication no` - 禁用密碼認證
- `ChallengeResponseAuthentication no` - 禁用挑戰回應認證
- `UsePAM no` - 禁用 PAM 認證
- `PubkeyAuthentication yes` - 啟用公鑰認證

### 🚨 緊急救援
如果意外被鎖定在伺服器外：
1. 檢查 VPS 提供商是否有控制面板或 VNC 存取
2. 使用備份的 SSH 配置檔案恢復設定
3. 聯繫 VPS 提供商的技術支援

## 故障排除

### 問題：ssh-copy-id 命令不存在
**解決方案：** 腳本會自動使用手動複製方法

### 問題：Permission denied (publickey)
**可能原因：**
- 公鑰未正確複製到伺服器
- 私鑰檔案權限不正確
- SSH 配置錯誤

**解決方案：**
```bash
# 檢查私鑰權限
chmod 600 ~/.ssh/id_ed25519_vps

# 重新執行設置腳本
./setup_ssh_vps.sh username vps_host
```

### 問題：SSH 服務重啟失敗
**解決方案：** 腳本會自動還原備份的配置檔案

## 需要協助？
如果遇到問題，請檢查：
1. 網路連線是否正常
2. VPS 是否正在運行
3. 使用者名稱和 IP 位址是否正確
4. 防火牆設定是否阻擋 SSH 連線（通常是 22 port） 