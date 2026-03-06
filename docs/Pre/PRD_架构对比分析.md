# 培训课程管理自动化系统 — 产品需求文档 (PRD)
## 三种架构方案对比分析

**项目名称**: Control de Formación — 培训课程管理自动化系统
**文档版本**: v1.0
**日期**: 2026-03-02
**作者**: 技术架构分析报告

---

## 一、项目背景与核心需求

### 1.1 业务场景

每个考核周期结束后，质量部门需要：
1. 将一份包含所有被考核人员评估数据的汇总 Excel 文件，按照 **Tutor（辅导员）** 拆分为若干独立文件
2. 向每位 Tutor 发送个性化邮件，附件包含其名下学员的评估数据
3. 邮件正文包含标准化说明文字 + Excel 数据截图预览

### 1.2 核心功能需求

| 功能模块 | 详细描述 |
|---------|---------|
| **F1. Excel 解析** | 上传汇总文件 → 自动识别第1-3行多级表头 → 识别 Tutor 列 |
| **F2. 文件拆分** | 按 Tutor 分组，生成独立 Excel，**完整保留原始格式、颜色、合并单元格、条件格式** |
| **F3. 邮件模板编辑器** | 富文本编辑器（所见即所得），支持动态变量、图片插入、格式调整，以 HTML 格式保存 |
| **F4. 邮件发送** | 通过 Power Automate 发送，正文为 HTML，附件为拆分 Excel，正文内嵌数据截图 |
| **F5. 文件下载** | 一键下载所有拆分文件的 ZIP 包 |
| **F6. 缓存清理** | 邮件发送完成后自动删除服务器临时文件 |

### 1.3 数据结构参考（基于 Resumen Calificaciones 工作表）

```
行1-3: 三级嵌套表头（合并单元格，不同背景色）
  - 第1行: 顶层分类（如 Formación、CTP、Revisión en vuelo 等）
  - 第2行: 次级分类（合并单元格，35.45pt 行高）
  - 第3行: 具体字段名（66pt 行高，黄色背景）
行4起: 数据行（D-I 列冻结，D4:BR 为数据区域）

关键列:
  D列: Profesional（被评估人姓名）
  E列: DNI（证件号）
  F列: MAIL（被评估人邮箱）
  AD列左右: Tutor（辅导员姓名）—— 拆分依据
  BI列: 最终评级（1-4分制）

样式特征:
  - 213个独立单元格样式
  - 25个合并单元格区域
  - 14条条件格式规则
  - 9列左侧冻结
```

### 1.4 邮件模板参考（基于 .msg 文件分析）

```
发件人: Elena Cervera / Verónica Paniagua
收件人: 各 Tutor 邮箱
抄送: Rosa Quispe
主题: Evaluación de la Competencia de Calidad_FINAL YEAR 24/25

正文结构:
  1. 称呼（动态: "Buenas tardes [Tutor名]"）
  2. 评级说明（1-4分制定义）
  3. 必修课程列表
  4. 评估维度说明（培训出勤 + CTP参与 + 飞行审阅）
  5. 加减分项说明
  6. INTEGRHO 系统操作指引（含截图）
  7. 落款签名

动态变量: {{tutor_name}}, {{tutor_email}}, {{year}}, {{attached_excel}}
```

---

## 二、评估维度定义

三种架构将从以下三个核心维度进行评分：

| 维度 | 权重 | 说明 |
|-----|-----|-----|
| **数据安全** | ★★★★★ | 员工个人数据、评估成绩不得泄露或被第三方访问 |
| **维护便利性** | ★★★★☆ | 无需专业IT团队即可更新模板、配置参数 |
| **用户调整弹性** | ★★★★☆ | 非技术人员可自主修改邮件模板、调整拆分规则 |

---

---

# 架构方案 A

## 全栈 Web 应用 + Power Automate HTTP 触发器

---

### A.1 架构概览

```
┌─────────────────────────────────────────────────────┐
│                   用户浏览器                          │
│   React 前端 (富文本编辑 / 文件上传 / 预览)           │
└─────────────────────┬───────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────┐
│              Ubuntu 服务器                            │
│   FastAPI (Python)                                   │
│   ├── Excel 解析模块 (openpyxl / pandas)             │
│   ├── 格式复制模块 (样式/条件格式/合并单元格)          │
│   ├── 截图生成模块 (xlwings / LibreOffice headless)   │
│   ├── ZIP 打包模块                                    │
│   ├── 邮件模板存储 (HTML 文件)                        │
│   └── 临时文件管理 (自动清理)                         │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP POST (JSON Payload)
┌─────────────────────▼───────────────────────────────┐
│              Power Automate                          │
│   HTTP 触发器 → 邮件发送 (Outlook/Exchange)          │
│   接收: 收件人、主题、HTML正文、附件(Base64)           │
└──────────────────────────────────────────────────────┘
```

### A.2 技术栈

| 层次 | 技术选型 |
|-----|---------|
| **前端** | React + Quill.js（富文本编辑器）+ TailwindCSS |
| **后端** | Python 3.11 + FastAPI + Uvicorn |
| **Excel 处理** | openpyxl（格式复制）+ pandas（数据操作）|
| **截图生成** | LibreOffice headless 转 PDF → 裁剪为图片，或 xlwings（需 Excel） |
| **邮件触发** | Power Automate HTTP 触发器（Premium 连接器）|
| **文件存储** | 本地临时目录（/tmp/formacion/），处理完毕后删除 |
| **部署** | Docker Compose on Ubuntu Server |

### A.3 详细功能设计

#### F1. Excel 上传与解析

```python
# 后端处理流程
POST /api/upload
  → 接收 multipart/form-data
  → openpyxl 加载工作簿（data_only=False 保留公式引用）
  → 识别 "Resumen Calificaciones" sheet
  → 扫描第1-3行，提取合并单元格信息 + 列标题映射
  → 自动检测 Tutor 列（扫描第3行匹配 "Tutor" 关键词）
  → 返回: 列映射预览 + Tutor 列表 + 数据行数

GET /api/preview/{upload_id}
  → 返回检测到的表头结构（JSON）
  → 前端展示列映射供用户确认
```

#### F2. Excel 拆分（保留完整格式）

```python
# 格式复制策略
def copy_with_full_format(source_ws, target_ws, rows):
    # 1. 复制列宽
    for col, dim in source_ws.column_dimensions.items():
        target_ws.column_dimensions[col] = copy(dim)

    # 2. 复制行高
    for row_num, dim in source_ws.row_dimensions.items():
        target_ws.row_dimensions[row_num] = copy(dim)

    # 3. 复制合并单元格（仅第1-3行保留全部合并，数据行不合并）
    for merged_range in source_ws.merged_cells.ranges:
        target_ws.merge_cells(str(merged_range))

    # 4. 逐单元格复制：值 + 样式（字体/填充/边框/对齐/数字格式）
    for row in rows:
        for cell in row:
            new_cell = target_ws[cell.coordinate]
            new_cell.value = cell.value
            if cell.has_style:
                new_cell.font = copy(cell.font)
                new_cell.fill = copy(cell.fill)
                new_cell.border = copy(cell.border)
                new_cell.alignment = copy(cell.alignment)
                new_cell.number_format = cell.number_format

    # 5. 复制条件格式规则
    for cf in source_ws.conditional_formatting._cf_rules.items():
        target_ws.conditional_formatting.add(cf[0], cf[1])

    # 6. 复制冻结窗格
    target_ws.freeze_panes = source_ws.freeze_panes
```

#### F3. 邮件模板编辑器

- **编辑器**: Quill.js（支持图片插入、格式刷、颜色、字体大小）
- **存储**: 以 HTML 文件保存在服务器，文件名格式 `template_v{n}.html`
- **动态变量**: 使用 `{{variable}}` 占位符，支持变量:
  - `{{tutor_nombre}}` — Tutor 姓名
  - `{{tutor_email}}` — Tutor 邮箱
  - `{{año_evaluacion}}` — 评估年度
  - `{{num_profesionales}}` — 名下学员数量
- **版本管理**: 保存历史版本，支持一键回退

#### F4. 截图生成

```bash
# 方案: LibreOffice headless（Ubuntu 服务器上可安装）
libreoffice --headless --convert-to pdf --outdir /tmp/ output.xlsx
# 再用 pdf2image 裁剪出数据区域
```

#### F5. 发送流程

```
用户点击"发送"
  → 后端循环每位 Tutor
    → 渲染 HTML 模板（替换变量）
    → 读取对应拆分 Excel（Base64 编码）
    → 生成数据截图（Base64 编码）
    → POST 到 Power Automate HTTP 触发器 URL
      {
        "to": "tutor@company.com",
        "cc": "rosa.quispe@forvismazars.com",
        "subject": "Evaluación...",
        "html_body": "<html>...</html>",
        "attachment_name": "Evaluacion_JuanBerral.xlsx",
        "attachment_content": "base64...",
        "screenshot_content": "base64..."
      }
    → Power Automate 解析并通过 Outlook 发送
  → 全部发送完毕 → 清理 /tmp 目录
  → 前端显示发送报告（成功/失败列表）
```

### A.4 Power Automate 配置（架构 A）

```
触发器: 当收到 HTTP 请求 时
  ↓
操作1: 解析 JSON（提取 to, cc, subject, html_body, 附件等字段）
  ↓
操作2: 发送电子邮件（V2）
  - 收件人: @{triggerBody()?['to']}
  - 主题: @{triggerBody()?['subject']}
  - 正文(HTML): @{triggerBody()?['html_body']}
  - 附件内容: base64ToBinary(@{triggerBody()?['attachment_content']})
  ↓
操作3: 响应 HTTP 请求（200 OK）
```

### A.5 部署方案

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - ./templates:/app/templates
      - /tmp/formacion:/tmp/formacion
    environment:
      - POWER_AUTOMATE_URL=${PA_WEBHOOK_URL}
      - SECRET_KEY=${SECRET_KEY}
    restart: always

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    restart: always

  nginx:
    image: nginx:alpine
    ports: ["443:443", "80:80"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on: [api, frontend]
```

### A.6 安全设计

| 安全措施 | 实现方式 |
|---------|---------|
| **传输加密** | HTTPS + TLS 1.3 |
| **身份认证** | JWT Token + 登录页面（用户名/密码）|
| **文件隔离** | 每次上传生成 UUID 子目录，用户只能访问自己的文件 |
| **临时文件** | 发送完成后立即删除，最长保留24小时（cron job 兜底）|
| **Power Automate URL** | URL 存储为环境变量，不暴露在前端代码中 |
| **访问日志** | Nginx 日志 + 应用层操作日志 |

---

### A.7 架构 A 评分

| 维度 | 评分 | 说明 |
|-----|-----|------|
| **数据安全** | ⭐⭐⭐⭐☆ | 数据仅在自有服务器处理，不经过第三方；但需自行维护服务器安全 |
| **维护便利性** | ⭐⭐⭐⭐☆ | Docker 部署，更新方便；需要具备基本 Python 知识进行调整 |
| **用户调整弹性** | ⭐⭐⭐⭐⭐ | 富文本编辑器完全可视化操作；列映射可界面配置；无需改代码 |

**总分: 13/15**

---

---

# 架构方案 B

## SharePoint + Power Automate 全程托管（低代码方案）

---

### B.1 架构概览

```
┌─────────────────────────────────────────────────────┐
│           Power Apps（前端界面）                      │
│   文件上传控件 / 预览 / 模板编辑 / 发送按钮           │
└──────┬──────────────────────────┬───────────────────┘
       │                          │
       ▼                          ▼
┌──────────────┐        ┌─────────────────────────────┐
│  SharePoint  │        │     Power Automate           │
│  Document    │        │  Flow 1: Excel 解析+拆分     │
│  Library     │        │  Flow 2: 截图生成             │
│  (文件存储)   │        │  Flow 3: 邮件发送             │
└──────┬───────┘        └──────────────────────────────┘
       │
       ▼
  [Python 脚本]  ← Ubuntu 服务器（仅做 Excel 格式处理）
  运行于 Azure
  Functions 或
  服务器上的
  HTTP 接口
```

> **注意**: Power Automate 原生 Excel 操作能力有限（仅能读写数值，无法复制样式），因此 Excel 拆分核心逻辑仍需 Python 处理。本架构将 Python 服务缩减为纯 API 无状态处理，文件存储迁移至 SharePoint。

### B.2 技术栈

| 层次 | 技术选型 |
|-----|---------|
| **前端** | Power Apps（Canvas App）|
| **文件存储** | SharePoint Document Library |
| **Excel 处理** | Python HTTP API（Ubuntu 服务器，无状态）|
| **流程编排** | Power Automate Premium |
| **邮件发送** | Power Automate → Outlook 365 |
| **模板存储** | SharePoint List（HTML 内容存入列表列）|
| **截图** | Power Automate + 截图服务 或 Python API |

### B.3 详细功能设计

#### 工作流设计

```
[用户在 Power Apps 上传文件]
  ↓ 文件保存至 SharePoint 文件库 /Input/
  ↓
[触发 Power Automate Flow 1: 解析拆分]
  → 调用 Ubuntu Python API: POST /parse-excel
    body: { sharepoint_file_url: "..." }
  → Python API 从 SharePoint 下载文件
  → 执行解析 + 拆分 + 格式复制
  → 将拆分后文件上传至 SharePoint /Output/{upload_id}/
  → 返回 Tutor 列表 + 文件路径映射
  ↓
[Flow 2: 截图生成]
  → 对每个拆分 Excel 调用 Python 截图 API
  → 截图存入 SharePoint /Screenshots/
  ↓
[用户在 Power Apps 预览、确认、编辑模板]
  ↓
[用户点击发送 → 触发 Flow 3: 邮件发送]
  → 循环 Tutor 列表
  → 从 SharePoint 读取对应 Excel 文件（Base64）
  → 从 SharePoint 读取对应截图
  → 渲染 HTML 模板（替换变量）
  → 发送邮件（Outlook 365 连接器）
  ↓
[Flow 4: 清理]
  → 删除 SharePoint /Input/ 和 /Output/ 中的临时文件
```

#### Power Apps 界面设计

```
页面1: 上传页
  - 文件上传控件（限 .xlsx）
  - 上传进度指示
  - 预览检测到的列映射（Gallery 控件显示表格）
  - "确认并继续" 按钮

页面2: 模板编辑
  - 富文本编辑器控件（Power Apps 内置 Rich Text Editor）
  - 变量插入按钮（点击插入 {{tutor_nombre}} 等占位符）
  - 图片上传（存入 SharePoint，URL 嵌入 HTML）
  - 预览模式切换
  - "保存模板" / "保存并发送" 按钮

页面3: 发送状态
  - Tutor 列表 + 发送状态（✓/✗/进行中）
  - 错误详情展开
  - "下载 ZIP" 按钮（触发 Power Automate 打包 Flow）
```

### B.4 安全设计

| 安全措施 | 实现方式 |
|---------|---------|
| **访问控制** | 依赖 Microsoft 365 账户权限体系（AAD） |
| **文件权限** | SharePoint 权限组，仅授权用户可访问上传文件夹 |
| **数据留存** | SharePoint 保留时间可配置，发送后自动删除 |
| **审计日志** | Power Automate 运行历史 + SharePoint 访问日志 |
| **API 安全** | Ubuntu Python API 仅接受来自 Power Automate 的请求（IP 白名单 + API Key）|

### B.5 限制与注意事项

1. **Power Apps 富文本编辑器** 功能相对有限（不支持所有 HTML 标签，图片处理受限）
2. **Power Automate Premium** 许可证要求（HTTP 连接器为 Premium 功能，~$15/用户/月）
3. **Excel 格式复制** 仍必须走 Python API，无法纯 Power Automate 实现
4. **截图生成** 在 Power Automate 中无原生支持，需借助 Python 或第三方服务

---

### B.6 架构 B 评分

| 维度 | 评分 | 说明 |
|-----|-----|------|
| **数据安全** | ⭐⭐⭐⭐⭐ | 完全在 Microsoft 企业生态内，AAD 权限管控，企业级合规 |
| **维护便利性** | ⭐⭐⭐☆☆ | Power Automate Flow 图形化维护方便；Python API 仍需技术支持；SharePoint 结构需规划 |
| **用户调整弹性** | ⭐⭐⭐☆☆ | Power Apps 富文本编辑器功能受限；修改 Flow 需要 Power Platform 经验 |

**总分: 11/15**

---

---

# 架构方案 C

## 轻量化混合架构：Python 处理引擎 + SharePoint 存储 + Power Automate 发送

---

### C.1 架构概览

```
┌─────────────────────────────────────────────────────┐
│           浏览器前端（轻量化 Vue.js / Nuxt）           │
│   Quill.js 富文本 / 文件上传 / 拆分预览 / 发送控制    │
└─────────────────────┬───────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────┐
│         Ubuntu 服务器（Python FastAPI）               │
│   ┌─────────────────────────────────────────────┐   │
│   │  Excel 引擎: 解析 → 拆分 → 格式复制 → 截图   │   │
│   ├─────────────────────────────────────────────┤   │
│   │  模板引擎: HTML 渲染 + 变量替换              │   │
│   ├─────────────────────────────────────────────┤   │
│   │  ZIP 引擎: 文件打包下载                      │   │
│   └─────────────────────────────────────────────┘   │
│                                                      │
│   处理完成后 → 上传拆分文件至 SharePoint             │
└──────────┬───────────────────────────┬──────────────┘
           │ Graph API                 │ HTTP Trigger
           ▼                           ▼
┌──────────────────┐         ┌────────────────────────┐
│   SharePoint     │         │   Power Automate       │
│   /Output/       │◄────────│   读取 SP 文件         │
│   （长期归档）    │         │   → 发送 Outlook 邮件  │
└──────────────────┘         └────────────────────────┘
```

### C.2 技术栈

| 层次 | 技术选型 | 说明 |
|-----|---------|-----|
| **前端** | Vue 3 + Quill.js + Element Plus | 轻量，部署在同一 Ubuntu 服务器 |
| **后端** | Python 3.11 + FastAPI | 所有核心逻辑 |
| **Excel 处理** | openpyxl + xlsxwriter | 格式精确复制 |
| **截图** | LibreOffice headless + pdf2image | 无需 Windows/Excel 环境 |
| **文件归档** | Microsoft Graph API → SharePoint | 处理完成后存档，便于追溯 |
| **邮件发送** | Power Automate（SharePoint 触发 or HTTP）| 仅负责发送，不负责处理 |
| **模板存储** | 服务器本地 JSON/HTML 文件 + 版本控制 | 轻量、可直接编辑 |

### C.3 核心设计思路

**职责分离原则**:
- Ubuntu 服务器 = 数据处理中心（Excel/截图/模板渲染）
- SharePoint = 文件归档仓库（长期保存、供 Tutor 下载追溯）
- Power Automate = 邮件发送渠道（利用其 Outlook 权限）

### C.4 详细功能设计

#### Excel 拆分模块（最完整实现）

```python
class ExcelSplitter:
    def __init__(self, source_path: str):
        self.wb = load_workbook(source_path)
        self.ws = self.wb["Resumen Calificaciones"]

    def detect_headers(self) -> dict:
        """解析三级表头结构"""
        header_map = {}
        for col in range(1, self.ws.max_column + 1):
            col_letter = get_column_letter(col)
            row1 = self.ws[f"{col_letter}1"].value
            row2 = self.ws[f"{col_letter}2"].value
            row3 = self.ws[f"{col_letter}3"].value
            header_map[col_letter] = {
                "level1": row1, "level2": row2, "level3": row3
            }
        return header_map

    def detect_tutor_column(self) -> str:
        """自动检测 Tutor 列"""
        for col in range(1, self.ws.max_column + 1):
            for row in range(1, 4):
                cell = self.ws.cell(row=row, column=col)
                if cell.value and "tutor" in str(cell.value).lower():
                    return get_column_letter(col)
        return None

    def split_by_tutor(self, tutor_col: str) -> dict:
        """按 Tutor 分组数据行"""
        tutor_groups = defaultdict(list)
        for row in self.ws.iter_rows(min_row=4, values_only=False):
            tutor_cell = row[column_index_from_string(tutor_col) - 1]
            tutor_name = str(tutor_cell.value).strip() if tutor_cell.value else "Sin_Tutor"
            tutor_groups[tutor_name].append(row)
        return tutor_groups

    def generate_split_file(self, tutor_name: str, data_rows: list) -> str:
        """生成带完整格式的拆分文件"""
        new_wb = Workbook()
        new_ws = new_wb.active

        # 复制所有列宽行高
        self._copy_dimensions(self.ws, new_ws)

        # 复制三级表头（第1-3行，含所有格式）
        self._copy_rows(self.ws, new_ws, source_rows=[1, 2, 3], target_start=1)

        # 复制合并单元格（仅表头区域）
        self._copy_merged_cells(self.ws, new_ws, max_row=3)

        # 复制该 Tutor 的数据行
        self._copy_rows(self.ws, new_ws,
                       source_rows=data_rows,
                       target_start=4)

        # 复制条件格式规则
        self._copy_conditional_formatting(self.ws, new_ws)

        # 复制冻结窗格
        new_ws.freeze_panes = self.ws.freeze_panes

        # 保存
        safe_name = re.sub(r'[^\w\s-]', '', tutor_name).strip()
        output_path = f"/tmp/formacion/{self.session_id}/{safe_name}.xlsx"
        new_wb.save(output_path)
        return output_path
```

#### 截图生成模块

```python
class ExcelScreenshot:
    """使用 LibreOffice headless 生成 Excel 截图"""

    def generate(self, xlsx_path: str, output_dir: str) -> str:
        # Step 1: xlsx → pdf
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", output_dir, xlsx_path
        ], check=True)

        # Step 2: pdf 第一页 → 裁剪图片（数据区域）
        pdf_path = xlsx_path.replace(".xlsx", ".pdf")
        images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)

        # Step 3: 裁剪（去除空白边距，保留表格主体）
        img = images[0]
        img_cropped = self._auto_crop(img)

        img_path = xlsx_path.replace(".xlsx", ".png")
        img_cropped.save(img_path, "PNG", optimize=True)
        return img_path

    def _auto_crop(self, img):
        """自动裁剪白边"""
        import numpy as np
        arr = np.array(img)
        # 找到非白色区域边界
        non_white = np.any(arr < 250, axis=2)
        rows = np.any(non_white, axis=1)
        cols = np.any(non_white, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        padding = 20
        return img.crop((
            max(0, cmin-padding), max(0, rmin-padding),
            min(img.width, cmax+padding), min(img.height, rmax+padding)
        ))
```

#### 邮件发送流程

```python
# 1. 前端点击发送
# 2. 后端准备所有 Tutor 数据包
# 3. 发送到 Power Automate（批量或逐条）

async def send_via_power_automate(
    tutor: TutorData,
    html_template: str,
    excel_path: str,
    screenshot_path: str,
    pa_webhook_url: str
):
    # 渲染 HTML（变量替换）
    html_body = html_template \
        .replace("{{tutor_nombre}}", tutor.name) \
        .replace("{{año_evaluacion}}", "2024/25") \
        .replace("{{num_profesionales}}", str(len(tutor.data_rows)))

    # 嵌入截图（Base64 inline）
    with open(screenshot_path, "rb") as f:
        screenshot_b64 = base64.b64encode(f.read()).decode()
    html_body += f'<br><img src="data:image/png;base64,{screenshot_b64}" style="max-width:100%"/>'

    # Excel 附件
    with open(excel_path, "rb") as f:
        excel_b64 = base64.b64encode(f.read()).decode()

    # 上传到 SharePoint（归档）
    sharepoint_url = await upload_to_sharepoint(excel_path, tutor.name)

    # 触发 Power Automate
    payload = {
        "to": tutor.email,
        "cc": "rosa.quispe@forvismazars.com",
        "subject": f"Evaluación de la Competencia de Calidad_FINAL YEAR 24/25",
        "html_body": html_body,
        "attachment": {
            "name": f"Evaluacion_{tutor.safe_name}.xlsx",
            "content": excel_b64
        }
    }

    async with aiohttp.ClientSession() as session:
        await session.post(pa_webhook_url, json=payload)
```

### C.5 SharePoint 归档集成

```python
# 使用 Microsoft Graph API 上传文件
from msgraph import GraphServiceClient
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id=TENANT_ID,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)
graph_client = GraphServiceClient(credential)

async def upload_to_sharepoint(file_path: str, tutor_name: str):
    site_id = "your-site-id"
    drive_id = "your-drive-id"
    folder_path = f"Control_Formacion/{datetime.now().strftime('%Y-%m')}"

    with open(file_path, "rb") as f:
        content = f.read()

    # 创建上传会话（支持大文件）
    result = await graph_client.drives \
        .by_drive_id(drive_id) \
        .items \
        .by_drive_item_id(f"root:/{folder_path}/{os.path.basename(file_path)}:") \
        .content \
        .put(content)

    return result.web_url
```

### C.6 安全设计

| 安全措施 | 实现方式 |
|---------|---------|
| **传输加密** | HTTPS + TLS 1.3（Nginx 反代）|
| **身份认证** | 可选: 集成 Microsoft SSO（Azure AD OIDC）或简单用户名/密码 |
| **临时文件** | UUID 隔离目录，发送后立即删除，最长保留6小时 |
| **SharePoint 权限** | App-only 权限（最小权限原则，仅 Files.ReadWrite.All）|
| **Power Automate URL** | 环境变量存储，定期轮换 |
| **数据不过第三方** | Excel 处理全在自有服务器，Power Automate 仅发邮件（不存数据）|

### C.7 架构 C 评分

| 维度 | 评分 | 说明 |
|-----|-----|------|
| **数据安全** | ⭐⭐⭐⭐⭐ | 处理在自有服务器，存档在企业 SharePoint，双重保障 |
| **维护便利性** | ⭐⭐⭐⭐⭐ | 职责清晰，Excel 引擎/邮件/存档相互独立，局部升级互不影响 |
| **用户调整弹性** | ⭐⭐⭐⭐⭐ | 完整富文本编辑器 + 列映射界面配置 + SharePoint 文件追溯 |

**总分: 15/15**

---

---

## 三、架构综合对比总表

| 对比维度 | 架构 A（全栈 Web）| 架构 B（Power Platform 为主）| 架构 C（混合最优）|
|---------|-----------------|---------------------------|-----------------|
| **数据安全** | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **维护便利性** | ⭐⭐⭐⭐☆ | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐⭐ |
| **用户调整弹性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐⭐ |
| **综合总分** | 13/15 | 11/15 | **15/15** |
| **初始开发成本** | 中 | 低（但 Premium 许可证贵）| 中高 |
| **运行成本** | 服务器费用 | Power Automate Premium 许可证 | 服务器费用 + Graph API（免费）|
| **技术依赖** | Python + React | Power Platform + Python | Python + Vue + SharePoint |
| **Excel 格式保真度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐⭐ |
| **邮件 HTML 保真度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐⭐ |
| **无微软权限限制** | ✅ 完全绕过 | ⚠️ 需 Premium 许可证 | ✅ 完全绕过 + 可选归档 |

---

## 四、详细优劣分析

### 架构 A — 优势与劣势

**优势**:
- 技术栈简洁，Python + React 开发生态成熟，人才丰富
- 完全自主控制，不依赖 Microsoft 许可证费用
- 富文本编辑器（Quill.js）功能完整，HTML 邮件保真度最高
- Excel 格式复制完整（openpyxl 直接操作底层 XML）

**劣势**:
- 文件处理完成后无持久化存储（除非额外接 SharePoint）
- 服务器安全需自行维护（防火墙/SSL证书/系统更新）
- 无历史发送记录的审计存档（除非自建日志系统）

**适合场景**: 组织没有 Microsoft 365 订阅或 SharePoint，或希望完全脱离微软生态的情况

---

### 架构 B — 优势与劣势

**优势**:
- 完全在 Microsoft 企业生态内，符合企业合规要求
- 文件自动存储在 SharePoint，有完整版本历史
- Power Automate 可视化 Flow 无需写代码维护
- 使用企业 Microsoft 365 账户身份验证，无需额外登录系统

**劣势**:
- Power Apps 富文本编辑器功能极其有限，无法满足复杂 HTML 邮件需求
- Power Automate HTTP 连接器需要 Premium 许可证（额外成本）
- Excel 格式复制仍无法脱离 Python，架构优势被削弱
- Flow 调试困难，出错排查复杂
- Power Automate 有请求次数和执行时长限制

**适合场景**: 组织有完整 Microsoft 365 E3/E5 订阅，IT 部门有 Power Platform 经验，且对邮件格式要求不高

---

### 架构 C — 优势与劣势

**优势**:
- **最高数据安全**: Excel 敏感数据全程在自有服务器处理，Power Automate 只收到 Base64 附件，不分析内容；SharePoint 归档享受企业级权限管控
- **最佳职责分离**: 每个组件只做自己最擅长的事（Python处理→SharePoint存档→Power Automate发送）
- **最高用户弹性**: 完整的 Quill.js 富文本编辑器，界面可配置列映射，模板支持版本历史
- **最容易维护**: 各模块独立，修改 Excel 逻辑不影响邮件发送，更换邮件渠道不影响文件处理
- **可选归档**: SharePoint 归档可选择开启/关闭，不影响核心流程

**劣势**:
- 需要配置 Azure App Registration（获取 Graph API 权限），有一定技术门槛
- 初期开发工作量略高于架构 A

**适合场景**: 组织有 Microsoft 365 订阅（SharePoint）但无 Power Automate Premium，希望数据安全和用户体验两者兼顾

---

## 五、推荐结论

**推荐选择架构 C（混合最优架构）**

理由:
1. **数据安全**: 员工评估数据（含 DNI、绩效分数）属于高度敏感信息，必须确保只在自有服务器和企业 SharePoint 之间流转，不经过任何第三方云服务
2. **维护便利**: 每个模块职责清晰，当业务规则变化（如新增考核维度、更换邮件模板）时，只需修改对应模块
3. **用户弹性**: 非技术用户可通过 UI 完成所有操作（上传、预览、编辑模板、发送、下载）；列映射可界面配置，无需改代码
4. **成本效益**: 仅需服务器运行成本，Graph API 在标准 Microsoft 365 许可证下免费使用

---

## 六、下一步行动（以架构 C 为基础）

| 阶段 | 工作内容 | 预计工作量 |
|-----|---------|-----------|
| **Phase 1: 环境搭建** | Ubuntu 服务器配置、Docker、LibreOffice headless | 1天 |
| **Phase 2: Excel 引擎** | 解析模块、拆分模块、格式复制、截图生成 | 3-5天 |
| **Phase 3: 前端界面** | Vue.js 界面、Quill.js 编辑器、文件上传预览 | 3-4天 |
| **Phase 4: 邮件集成** | Power Automate Flow 配置、HTML 模板系统 | 2天 |
| **Phase 5: SharePoint 归档** | Graph API 集成、文件上传下载 | 1-2天 |
| **Phase 6: 测试与优化** | 端到端测试、格式验证、性能优化 | 2天 |

---

*文档版本 v1.0 | 基于 ejemplo 文件夹实际数据分析生成*
