你是一个高级 Python 开发工程师。你需要基于已有的 PRD、技术规范和原型代码，构建一个符合标准规范的完整项目。

## 参考文档（必须全部读取后再开始编码）

按以下顺序读取并理解：

1. `/docs/PRD.md` — 产品需求，理解业务逻辑和数据格式
2. `/docs/TECH_SPEC.md` — 技术规范，遵循项目结构、API 端点、数据模型
3. `/docs/ARCHITECTURE.md` — 架构设计，遵循分层架构和组件职责
4. `/docs/CONVENTIONS.md` — 编码规范，遵循命名、错误处理、日志等约定
5. `/Ejemplo/evaluaciones Auditoria_Gerente y Socios.xlsx` — 用来拆解的样本excel 文件
6. `/Ejemplo/` 下4个msg文件 — 发送邮件的内容样本，其中有相关的图片，这些资源需要提取并且作为预设的邮件内容

## 已有原型代码

`/P1/` 文件夹中包含已有的原型代码或部分实现。你需要：

1. 读取 P1/ 中所有文件，理解已实现的业务逻辑
2. 将可复用的逻辑提取并重构到标准项目结构中
3. 不要丢弃 P1 中已验证的核心逻辑（特别是 Excel 解析和数据处理部分）

## 构建要求

### 目标结构（以 / 为根目录）

/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── models/
│ ├── init.py
│ └── schemas.py
├── services/
│ ├── init.py
│ ├── excel_parser.py
│ ├── excel_generator.py
│ ├── contact_mapper.py
│ └── email_sender.py
├── static/
│ └── index.html
├── templates/
│ └── email_default.html
├── data/
│ └── .gitkeep
├── tests/
│ ├── test_parser.py
│ ├── test_generator.py
│ ├── test_mapper.py
│ └── test_sender.py
└── docs/
├── PRD.md
├── PRD_TEMPLATE.md
├── TECH_SPEC.md
├── ARCHITECTURE.md
└── CONVENTIONS.md


### 开发顺序

1. **config.py** — 参照 TECH_SPEC Section 4.2 创建 Settings 类，端口使用 PRD Section 13 指定的值
2. **models/schemas.py** — 参照 TECH_SPEC Section 6 创建数据模型，根据 PRD Section 4-5 添加 app 特有字段
3. **services/excel_parser.py** — 核心模块，从 P1 提取解析逻辑，重构为 TECH_SPEC Section 7.1 规定的接口
4. **services/excel_generator.py** — 从 P1 提取或新建，遵循 TECH_SPEC Section 7.2 接口
5. **services/contact_mapper.py** — 从 P1 提取或按 TECH_SPEC Section 7.3 实现
6. **services/email_sender.py** — 从 P1 提取或按 TECH_SPEC Section 7.4 实现，JSON payload 必须严格遵循 TECH_SPEC Section 8 的格式
7. **main.py** — 参照 TECH_SPEC Section 5 实现所有标准 API 端点
8. **static/index.html** — 参照 ARCHITECTURE Section 4 和 CONVENTIONS Section 5 构建前端 SPA
9. **templates/email_default.html** — 使用 PRD Section 6.2 定义的邮件模板
10. **Dockerfile + docker-compose.yml** — 参照 TECH_SPEC Section 15 和 DEPLOYMENT 指南
11. **requirements.txt** — 参照 TECH_SPEC Section 2
12. **.env.example** — 参照 TECH_SPEC Section 4.1，列出所有环境变量
13. **tests/** — 参照 CONVENTIONS Section 10，为每个 service 编写单元测试

### 编码规范（严格遵守）

- Python 命名：函数 snake_case、类 PascalCase、常量 UPPER_SNAKE_CASE
- API 路由：kebab-case（`/api/map-contacts`）
- 所有函数必须有 type hints
- 错误信息使用西班牙语
- 数字格式使用欧洲格式（1.234,56）
- 日志禁止记录 PII、邮件内容、Power Automate URL
- 前端全部内联在 index.html 中（CSS 在 <style>，JS 在 <script>），不引用外部 CDN

### 完成后

1. 确认所有文件已创建且代码可运行
2. 删除 `/P1/` 文件夹及其所有内容
3. 给出项目摘要：列出创建的文件、实现的端点、以及需要手动配置的项（如 .env 中的 POWER_AUTOMATE_URL）
