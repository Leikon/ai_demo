# DouK-Downloader 配置指南

## 📦 项目简介

抖音/TikTok 视频下载工具，支持批量下载、直播录制、AI 描述改写等功能。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 方式一：使用 uv（推荐）
uv sync --no-dev

# 方式二：使用 pip
pip install -r requirements.txt
```

### 2. 启动程序

```bash
# 使用 uv
uv run main.py

# 使用 python
python main.py
```

---

## ⚙️ 配置说明

配置文件位于：`Volume/settings.json`

### 必需配置：Cookie

Cookie 是程序运行的核心，没有 Cookie 无法获取数据。

**获取方式（三选一）：**

1. **从剪贴板读取（推荐）**
   - 浏览器登录抖音网页版
   - 按 `F12` 打开开发者工具 → `Application` → `Cookies`
   - 复制所有 Cookie 内容
   - 程序中选择「从剪贴板读取 Cookie」

2. **从浏览器读取**
   - 程序启动后选择此选项
   - Windows 需要以管理员身份运行

3. **手动填写**
   - 编辑 `Volume/settings.json` 中的 `cookie` 字段

**必需的 Cookie 字段：**
```json
{
    "cookie": {
        "sessionid": "",
        "sessionid_ss": "",
        "sid_guard": "",
        "sid_tt": "",
        "sid_ucp_v1": "",
        "uid_tt": "",
        "odin_tt": "",
        "ttwid": "",
        "passport_csrf_token": ""
    }
}
```

---

### 可选配置：MiMo API Key 也可以用别的openai的就行

用于 AI 功能（视频描述反推、改写等）。

```json
{
    "mimo_api_key": "你的API密钥",
    "mimo_model": "mimo-v2.5",
    "mimo_base_url": "https://token-plan-cn.xiaomimimo.com/v1"
}
```

**获取方式：**
1. 访问 [小米 MiMo 平台](https://api.xiaomimimo.com)
2. 注册账号并获取 API Key，glm也行（需要多模态，需要多模态！）


---

### 可选配置：FFmpeg

用于下载直播视频。

```json
{
    "ffmpeg": "C:\\path\\to\\ffmpeg.exe"
}
```

**安装方式：**
- 下载：https://ffmpeg.org/download.html
- 解压后将 `bin` 目录路径填入配置

---

### 可选配置：代理

访问 TikTok 需要代理。

```json
{
    "proxy": "http://127.0.0.1:7890",
    "proxy_tiktok": "http://127.0.0.1:7890"
}
```

---

### 可选配置：下载路径

```json
{
    "root": "",
    "folder_name": "Download"
}
```

- `root`：留空表示使用程序所在目录
- `folder_name`：下载文件夹名称

---

### 可选配置：文件命名格式

```json
{
    "name_format": "create_time type nickname desc",
    "desc_length": 64,
    "name_length": 128,
    "date_format": "%Y-%m-%d %H:%M:%S",
    "split": "-"
}
```

---

## 📁 完整配置示例

```json
{
    "accounts_urls": [],
    "mix_urls": [],
    "root": "",
    "folder_name": "Download",
    "name_format": "create_time type nickname desc",
    "cookie": {
        "sessionid": "你的sessionid",
        "sessionid_ss": "你的sessionid_ss",
        "sid_guard": "你的sid_guard",
        "sid_tt": "你的sid_tt",
        "uid_tt": "你的uid_tt",
        "odin_tt": "你的odin_tt"
    },
    "mimo_api_key": "",
    "ffmpeg": "",
    "proxy": "",
    "download": true
}
```

---

## 🎯 使用示例

### 下载单个视频

1. 启动程序
2. 选择「终端交互模式」
3. 选择「批量下载链接作品」
4. 粘贴抖音视频链接

### 批量下载账号作品

1. 在 `settings.json` 的 `accounts_urls` 中添加账号信息
2. 启动程序选择对应功能

```json
{
    "accounts_urls": [
        {
            "mark": "账号备注",
            "url": "https://www.douyin.com/user/xxx",
            "tab": "post",
            "earliest": "",
            "latest": "",
            "enable": true
        }
    ]
}
```

---

## ❓ 常见问题

### Q: Cookie 失效怎么办？

A: 重新获取 Cookie 并更新配置文件。

### Q: 无法下载最高清视频？

A: 更新 Cookie，使用已登录的 Cookie。

### Q: 程序运行报错？

A: 检查 Python 版本是否为 3.12，依赖是否安装完整。

### Q: 如何下载 TikTok 视频？

A: 需要配置代理 `proxy_tiktok` 并使用 TikTok 的 Cookie。

---

## 📝 注意事项

1. Cookie 仅需在失效后重新配置，无需每次运行都设置
2. 程序内置延时机制，避免请求过频
3. Windows 需管理员权限才能读取浏览器 Cookie
4. 按 `Ctrl + C` 可随时终止程序

---

## 🔗 相关链接

- [Cookie 获取教程](https://github.com/JoeanAmier/TikTokDownloader/blob/master/docs/Cookie获取教程.md)
- [项目文档](https://github.com/JoeanAmier/TikTokDownloader/wiki/Documentation)

---

## 📄 许可证

本项目基于 GPL-3.0 许可证开源。
