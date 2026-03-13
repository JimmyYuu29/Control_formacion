# control_formacion — systemd 服务器部署指南

> 适用系统：Ubuntu 20.04 / 22.04 / Debian 11+
> 应用版本：2.0.0
> 运行端口：8002
> 运行用户：`rootadmin`（与项目默认数据路径一致）

---

## 目录

1. [环境准备](#1-环境准备)
2. [安装系统依赖](#2-安装系统依赖)
3. [创建运行用户](#3-创建运行用户)
4. [部署应用代码](#4-部署应用代码)
5. [配置 Python 虚拟环境](#5-配置-python-虚拟环境)
6. [配置环境变量](#6-配置环境变量)
7. [准备数据目录](#7-准备数据目录)
8. [创建 systemd 服务文件](#8-创建-systemd-服务文件)
9. [启用并启动服务](#9-启用并启动服务)
10. [配置 Nginx 反向代理（可选）](#10-配置-nginx-反向代理可选)
11. [日常运维命令](#11-日常运维命令)
12. [故障排查](#12-故障排查)

---

## 1. 环境准备

### 1.1 确认系统版本

```bash
lsb_release -a
uname -m   # 应为 x86_64
```

### 1.2 更新系统包

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 2. 安装系统依赖

### 2.1 安装 Python 3.11

```bash
# Ubuntu 22.04 自带 Python 3.10，需要手动安装 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

验证安装：

```bash
python3.11 --version   # 应输出 Python 3.11.x
```

### 2.2 安装 LibreOffice（关键依赖）

> 应用使用 LibreOffice headless 将 Excel 转换为 PDF 再转 PNG 截图，**必须安装**。

```bash
sudo apt install -y libreoffice libreoffice-calc
```

验证安装：

```bash
libreoffice --version   # 应输出 LibreOffice 7.x.x
```

### 2.3 安装其他系统依赖

```bash
sudo apt install -y \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev
```

---

## 3. 创建运行用户

> 项目默认数据路径为 `/home/rootadmin/data/Control_formacion`，因此推荐使用 `rootadmin` 用户运行服务。

```bash
# 创建系统用户（如果不存在）
sudo useradd -m -s /bin/bash rootadmin

# 设置密码（可选，若不需要 SSH 登录可跳过）
sudo passwd rootadmin
```

---

## 4. 部署应用代码

### 4.1 选择部署目录

推荐将应用部署在 `/opt/control_formacion`：

```bash
sudo mkdir -p /opt/control_formacion
sudo chown rootadmin:rootadmin /opt/control_formacion
```

### 4.2 克隆或上传代码

**方式一：通过 Git 克隆**

```bash
sudo -u rootadmin git clone <YOUR_REPO_URL> /opt/control_formacion
```

**方式二：通过 SCP 上传**

在本地执行：

```bash
scp -r /path/to/control_formacion rootadmin@<SERVER_IP>:/opt/
```

### 4.3 确认文件结构

```bash
ls -la /opt/control_formacion
# 应包含：main.py, config.py, requirements.txt, static/, services/, models/ 等
```

---

## 5. 配置 Python 虚拟环境

```bash
# 切换到 rootadmin 用户
sudo -u rootadmin bash

# 进入项目目录
cd /opt/control_formacion

# 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate

# 退出 rootadmin shell
exit
```

验证安装：

```bash
sudo -u rootadmin /opt/control_formacion/venv/bin/python -c "import fastapi, uvicorn; print('OK')"
```

---

## 6. 配置环境变量

### 6.1 创建 .env 文件

```bash
sudo -u rootadmin cp /opt/control_formacion/.env.example /opt/control_formacion/.env
sudo -u rootadmin nano /opt/control_formacion/.env
```

### 6.2 .env 文件内容说明

```dotenv
# ============================================================
# 必填项
# ============================================================

# Power Automate webhook URL（用于发送邮件）
# 从 Power Automate 的 HTTP 触发器获取
POWER_AUTOMATE_URL=https://prod-xx.westeurope.logic.azure.com:443/workflows/xxx...

# ============================================================
# 服务器配置
# ============================================================

HOST=0.0.0.0
PORT=8002
DEBUG=false

# ============================================================
# 数据路径配置
# ============================================================

# 外部持久化数据根目录（temp/ 和 basedata/ 子目录会自动创建）
DATA_ROOT_PATH=/home/rootadmin/data/Control_formacion

# ============================================================
# 联系人数据配置
# ============================================================

# 联系人 Excel 文件路径（相对于项目目录）
CONTACTS_FILE_PATH=data/Contactos_Tutores.xlsx

# 联系人 JSON 存储路径
CONTACTS_STORE_PATH=data/contacts_store.json

# 删除联系人时需要的密码
CONTACTS_DELETE_PASSWORD=Formacion2026

# ============================================================
# 邮件配置
# ============================================================

# 默认抄送邮箱列表，多个用逗号分隔
DEFAULT_CC_EMAILS=admin@example.com,manager@example.com

# ============================================================
# 历史记录配置
# ============================================================

# 最大保留历史记录条数
MAX_HISTORY=10
```

### 6.3 保护 .env 文件权限

```bash
sudo chmod 600 /opt/control_formacion/.env
sudo chown rootadmin:rootadmin /opt/control_formacion/.env
```

---

## 7. 准备数据目录

```bash
# 创建应用内部 data 目录
sudo -u rootadmin mkdir -p /opt/control_formacion/data

# 创建外部持久化数据目录（必须与 DATA_ROOT_PATH 一致）
sudo -u rootadmin mkdir -p /home/rootadmin/data/Control_formacion/temp
sudo -u rootadmin mkdir -p /home/rootadmin/data/Control_formacion/basedata

# 如果已有联系人数据文件，上传到对应路径
# scp Contactos_Tutores.xlsx rootadmin@<SERVER>:/opt/control_formacion/data/

# 确认权限
ls -la /home/rootadmin/data/Control_formacion/
ls -la /opt/control_formacion/data/
```

---

## 8. 创建 systemd 服务文件

```bash
sudo nano /etc/systemd/system/control-formacion.service
```

粘贴以下内容：

```ini
[Unit]
Description=Control Formacion - Evaluation Splitter Service
Documentation=https://github.com/yourorg/control_formacion
After=network.target network-online.target
Wants=network-online.target

[Service]
# ---- 运行身份 ----
User=rootadmin
Group=rootadmin

# ---- 工作目录（必须是项目根目录，config.py 从此处读取 .env） ----
WorkingDirectory=/opt/control_formacion

# ---- 启动命令（单 worker：应用使用内存 session，不支持多进程） ----
ExecStart=/opt/control_formacion/venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 8002 \
    --workers 1 \
    --log-level info \
    --access-log

# ---- 重启策略 ----
Restart=always
RestartSec=5
StartLimitInterval=60
StartLimitBurst=3

# ---- 环境变量 ----
# 注意：.env 文件由 pydantic-settings 在应用内部自动加载
# 这里设置 PATH 确保 LibreOffice 可被找到
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="HOME=/home/rootadmin"

# ---- 超时配置 ----
TimeoutStartSec=30
TimeoutStopSec=30

# ---- 日志配置（日志由 journald 收集）----
StandardOutput=journal
StandardError=journal
SyslogIdentifier=control-formacion

# ---- 安全加固（可选，生产环境推荐）----
# 防止写入系统目录（数据目录已通过 ReadWritePaths 开放）
ProtectSystem=strict
ReadWritePaths=/opt/control_formacion/data
ReadWritePaths=/home/rootadmin/data/Control_formacion
ReadWritePaths=/tmp

# 防止进程获取新特权
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

---

## 9. 启用并启动服务

### 9.1 重载 systemd 配置

```bash
sudo systemctl daemon-reload
```

### 9.2 启用开机自启

```bash
sudo systemctl enable control-formacion.service
```

### 9.3 启动服务

```bash
sudo systemctl start control-formacion.service
```

### 9.4 验证服务状态

```bash
sudo systemctl status control-formacion.service
```

期望输出示例：

```
● control-formacion.service - Control Formacion - Evaluation Splitter Service
     Loaded: loaded (/etc/systemd/system/control-formacion.service; enabled; vendor preset: enabled)
     Active: active (running) since Fri 2026-03-13 10:00:00 UTC; 5s ago
   Main PID: 12345 (uvicorn)
      Tasks: 3 (limit: 4915)
     Memory: 120.5M
        CPU: 1.234s
     CGroup: /system.slice/control-formacion.service
             └─12345 /opt/control_formacion/venv/bin/python ...

Mar 13 10:00:00 server control-formacion[12345]: INFO:     Started server process [12345]
Mar 13 10:00:00 server control-formacion[12345]: INFO:     Waiting for application startup.
Mar 13 10:00:00 server control-formacion[12345]: INFO:     Application startup complete.
Mar 13 10:00:00 server control-formacion[12345]: INFO:     Uvicorn running on http://0.0.0.0:8002
```

### 9.5 验证应用响应

```bash
# 健康检查
curl -s http://localhost:8002/health | python3 -m json.tool

# 访问首页（应返回 HTML）
curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/
# 期望返回：200
```

---

## 10. 配置 Nginx 反向代理（可选）

如果需要通过域名访问，或在 80/443 端口上提供服务，配置 Nginx 反向代理。

### 10.1 安装 Nginx

```bash
sudo apt install -y nginx
```

### 10.2 创建站点配置

```bash
sudo nano /etc/nginx/sites-available/control-formacion
```

粘贴以下内容（HTTP 版本）：

```nginx
server {
    listen 80;
    server_name your-domain.com;   # 替换为你的域名或服务器 IP

    # 上传文件大小限制（Excel 文件可能较大）
    client_max_body_size 50M;

    # 代理超时（LibreOffice 转换可能耗时较长）
    proxy_read_timeout 120s;
    proxy_connect_timeout 10s;
    proxy_send_timeout 120s;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;

        # WebSocket 支持（如未来需要）
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 传递真实客户端 IP
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件可选择让 Nginx 直接处理（提升性能）
    location /static/ {
        alias /opt/control_formacion/static/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }
}
```

### 10.3 启用站点并重载 Nginx

```bash
sudo ln -s /etc/nginx/sites-available/control-formacion /etc/nginx/sites-enabled/
sudo nginx -t       # 检查配置语法
sudo systemctl reload nginx
```

### 10.4 配置 HTTPS（推荐，使用 Certbot）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Certbot 会自动修改 Nginx 配置并设置 HTTPS 证书自动续期。

---

## 11. 日常运维命令

### 服务控制

```bash
# 启动服务
sudo systemctl start control-formacion

# 停止服务
sudo systemctl stop control-formacion

# 重启服务
sudo systemctl restart control-formacion

# 重载（代码未变，仅重读配置）
sudo systemctl reload control-formacion

# 查看服务状态
sudo systemctl status control-formacion
```

### 查看日志

```bash
# 查看最新 100 行日志
sudo journalctl -u control-formacion -n 100

# 实时跟踪日志（类似 tail -f）
sudo journalctl -u control-formacion -f

# 查看今天的日志
sudo journalctl -u control-formacion --since today

# 查看指定时间段的日志
sudo journalctl -u control-formacion --since "2026-03-13 10:00:00" --until "2026-03-13 11:00:00"

# 只看错误级别日志
sudo journalctl -u control-formacion -p err
```

### 代码更新部署流程

```bash
# 1. 拉取新代码
sudo -u rootadmin bash -c "cd /opt/control_formacion && git pull"

# 2. 激活虚拟环境并更新依赖（如 requirements.txt 有变化）
sudo -u rootadmin bash -c "cd /opt/control_formacion && source venv/bin/activate && pip install -r requirements.txt"

# 3. 重启服务
sudo systemctl restart control-formacion

# 4. 确认服务正常
sudo systemctl status control-formacion
curl -s http://localhost:8002/health
```

### 检查端口占用

```bash
sudo ss -tlnp | grep 8002
# 或
sudo lsof -i :8002
```

---

## 12. 故障排查

### 问题 1：服务启动失败

**排查步骤：**

```bash
# 查看详细错误信息
sudo journalctl -u control-formacion -n 50 --no-pager

# 手动测试启动命令
sudo -u rootadmin bash -c "cd /opt/control_formacion && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8002 --workers 1"
```

**常见原因：**

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `ModuleNotFoundError` | 依赖未安装或虚拟环境路径错误 | 检查 `ExecStart` 中的 venv 路径，重新运行 `pip install -r requirements.txt` |
| `Address already in use` | 端口 8002 被占用 | `sudo ss -tlnp \| grep 8002` 查找占用进程并终止 |
| `Permission denied` | 用户无权限访问数据目录 | 检查 `ReadWritePaths` 配置，确认目录权限 |
| `POWER_AUTOMATE_URL not set` | .env 文件缺失或路径错误 | 确认 `.env` 文件在 `WorkingDirectory` 下 |

### 问题 2：LibreOffice 相关错误

```bash
# 验证 LibreOffice 是否可用
sudo -u rootadmin libreoffice --headless --version

# 如果提示 display 错误，添加 DISPLAY 环境变量
# 在 systemd 服务文件 [Service] 段添加：
# Environment="DISPLAY=:99"
# 并安装 Xvfb：
sudo apt install -y xvfb
```

### 问题 3：数据目录权限问题

```bash
# 检查目录权限
ls -la /opt/control_formacion/data/
ls -la /home/rootadmin/data/Control_formacion/

# 修复权限
sudo chown -R rootadmin:rootadmin /opt/control_formacion/data/
sudo chown -R rootadmin:rootadmin /home/rootadmin/data/Control_formacion/
sudo chmod -R 755 /home/rootadmin/data/Control_formacion/
```

### 问题 4：服务崩溃后不重启

检查 `StartLimitBurst` 是否触发：

```bash
# 查看服务是否进入失败状态
sudo systemctl status control-formacion

# 如果状态为 failed，重置失败计数器
sudo systemctl reset-failed control-formacion
sudo systemctl start control-formacion
```

### 问题 5：内存占用过高

LibreOffice 在转换文件时会产生较高内存占用。可以添加内存限制：

在 `[Service]` 段添加：

```ini
MemoryMax=1G
MemoryHigh=800M
```

---

## 附录：完整目录结构

部署完成后，服务器上的文件布局应如下：

```
/
├── etc/
│   └── systemd/
│       └── system/
│           └── control-formacion.service      # systemd 服务文件
├── opt/
│   └── control_formacion/                     # 应用代码
│       ├── .env                               # 环境变量（权限 600）
│       ├── main.py
│       ├── config.py
│       ├── requirements.txt
│       ├── venv/                              # Python 虚拟环境
│       ├── data/                              # 本地数据（联系人、预设）
│       │   ├── Contactos_Tutores.xlsx
│       │   ├── contacts_store.json
│       │   ├── column_presets.json
│       │   └── email_templates.json
│       ├── models/
│       ├── services/
│       ├── static/
│       └── templates/
└── home/
    └── rootadmin/
        └── data/
            └── Control_formacion/             # 外部持久化数据
                ├── temp/                      # 临时文件（每次运行）
                ├── basedata/                  # 数据备份
                └── history.json               # 操作历史
```

---

*文档生成日期：2026-03-13*
