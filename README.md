# 🚀 FreeXCraft 自动续期系统

> 通过 GitHub Actions 实现 FreeXCraft 服务器的 24/7 自动续期

---

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [核心变量说明](#核心变量说明)
- [准备工作](#准备工作获取-telegram-推送权限)
- [部署教程](#部署教程)
- [工作原理](#脚本如何模拟真人高级说明)
- [常见问题](#维护与排障)

---

## 📖 项目简介

FreeXCraft 是一款免费 Minecraft 服务器托管服务，但需要定期手动续期。本系统通过 GitHub Actions 实现**全自动化续期**，无需人工干预，服务器 7×24 小时稳定运行。

---

## ✨ 功能特性

| 功能 | 说明 |
| :--- | :--- |
| 🔄 自动续期 | GitHub Actions 定时执行，24/7 全自动 |
| 🎲 随机时间触发 | 每次运行时间随机，避免被检测 |
| 🖥️ 多浏览器指纹 | 随机模拟 Chrome、Edge、Safari 等 UA |
| ⏳ 行为模拟 | 登录后随机等待，模拟真人操作 |
| 📱 Telegram 推送 | 实时接收续期成功/失败通知 |

---

## 🔑 核心变量说明

系统涉及两部分配置：**GitHub Secrets（环境变量）** 和 **代码内固定参数**。

### 1. GitHub Secrets（必须配置）

在仓库 `Settings` → `Secrets and variables` → `Actions` 中添加：

| 变量名 | 必填 | 说明 |
| :--- | :---: | :--- |
| `FXC_EMAIL` | ✅ | FreeXCraft 登录邮箱 |
| `FXC_PASS` | ✅ | FreeXCraft 登录密码 |
| `TG_BOT_TOKEN` | ❌ | Telegram 机器人 API Token |
| `TG_CHAT_ID` | ❌ | 接收通知的个人 Telegram ID |

### 2. 代码内固定参数（renew.py 顶部）

| 参数名 | 类型 | 说明 |
| :--- | :---: | :--- |
| `SERVER_ID` | **个人唯一（必须修改）** | 服务器 ID（面板 URL 最后一段） |
| `ACTION_ID` | 全网通用 | 续期功能后端 ID，需用开发者工具抓取 |
| `SUPABASE_URL` | 全网通用 | 官方数据库 API 地址（已预设） |
| `ANON_KEY` | 全网通用 | 官方数据库通信密钥（已预设） |

> ⚠️ **`SERVER_ID` 是必须修改的参数！不修改将导致续期失败！**

---

## ⚠️ 重要：SERVER_ID 必须修改

### 📌 如何获取 SERVER_ID？

进入你的 FreeXCraft 服务器面板，查看浏览器地址栏：

```
https://freexcraft.com/dashboard/server/1ed88a77-8513-43f9-9d1e-3a0db85b84b5
                                                    ↑ 这一串就是 SERVER_ID
```

**示例**：根据 URL `https://freexcraft.com/dashboard/server/1ed88a77-8513-43f9-9d1e-3a0db85b84b5`

- 服务器 ID（SERVER_ID）= `1ed88a77-8513-43f9-9d1e-3a0db85b84b5`

### 🔴 警告：必须修改！

> ⚠️ **在上传 `renew.py` 之前，你必须将代码中的 `SERVER_ID` 修改为你自己的服务器 ID！**
>
> 如果不修改，脚本将会续期失败！

---

## 📱 准备工作：获取 Telegram 推送权限

### Step 1: 获取 Bot Token

1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示设置机器人名称
4. 获得 Token（如 `723456...:AAH_xxxx`）

### Step 2: 获取 Chat ID

1. 搜索并关注 `@userinfobot`
2. 发送任意消息
3. 返回的 `Id: 12345678` 即为 `TG_CHAT_ID`

### Step 3: 激活机器人

> ⚠️ **非常重要**：必须先给机器人发一条消息，它才有权限给你发送通知！

---

## 🚀 部署教程

### 步骤 1: 创建私有仓库

```
1. 登录 GitHub → New repository
2. Repository Name: AutoRenew_FXC（自定义）
3. 必须选择 Private（私有）
```

### 步骤 2: 配置 GitHub Secrets

```
仓库 → Settings → Secrets and variables → Actions → New repository secret
```

依次添加：

- `FXC_EMAIL`
- `FXC_PASS`
- `TG_BOT_TOKEN`（可选）
- `TG_CHAT_ID`（可选）

### 步骤 3: 上传核心脚本

在根目录创建 `renew.py`，粘贴完整代码。

> ⚠️ **【关键步骤】必须修改代码顶部的 `SERVER_ID` 为你自己的服务器 ID！**
>
> 例如：
> ```python
> SERVER_ID = "1ed88a77-8513-43f9-9d1e-3a0db85b84b5"  # 替换为你的服务器 ID
> ```


## 🧠 工作原理（高级说明）

为防止账号被封禁，脚本内置三重混淆逻辑：

```
┌─────────────────────────────────────────────────────────┐
│                      防封号策略                          │
├─────────────────────────────────────────────────────────┤
│  🎲 随机延迟触发    每次运行的具体分钟数随机              │
│  🖥️ 随机设备指纹    从多浏览器 UA 中随机抽取             │
│  ⏳ 行为间隙        登录后等待 5-15 秒模拟真人           │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 维护与排障

| 问题 | 解决方案 |
| :--- | :--- |
| 续费失败，提示 404 | FreeXCraft 网站已更新，用 F12 抓取新的 `ACTION_ID` |
| 时间解析报错 | 脚本已内置兼容函数，一般无需处理 |
| 没有 TG 通知 | 检查 Secrets 变量名是否一致，确认已给机器人发送过消息 |
| **续期到别人的服务器** | 检查 `SERVER_ID` 是否已修改为你自己的 ID |

---

## ⚠️ 安全注意事项

1. **严禁 Fork 公开仓库** - 防止账号被管理员爬取
2. **必须使用私有仓库** - 保护账号密码安全
3. **必须修改 SERVER_ID** - 不修改会续期失败
4. **定期检查** - 建议偶尔手动登录确认服务器状态

---

## 📄 许可证

本项目仅供学习交流使用，请遵守 FreeXCraft 服务条款。

---

## 🔗 参考链接

- FreeXCraft 面板：https://freexcraft.com
- 服务器面板示例：https://freexcraft.com/dashboard/server/1ed88a77-8513-43f9-9d1e-3a0db85b84b5

---

> ⚠️ **最后提醒**：上传 `renew.py` 前，请务必将 `SERVER_ID` 修改为你自己的服务器 ID！否则脚本将无效！
