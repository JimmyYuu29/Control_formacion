你是一个产品经理助手。我需要你根据我提供的项目描述信息，填写 PRD 模板并生成完整的 PRD 文档。

## 工作流程

1. 先读取 PRD 模板文件：`/项目名/docs/PRD_TEMPLATE.md`
2. 根据我下面提供的项目描述信息，填写模板中所有章节
3. 将填写完成的 PRD 写入：`/项目名/docs/PRD.md`（保留原始模板不动）

## 填写规则

- 删除模板中所有 `[bracketed instructions]` 说明文字
- 替换所有 `{placeholders}` 为实际内容
- 如果我的描述中没有提供某个章节所需的信息，根据上下文和同类项目经验合理推断填写，并在该处添加 `<!-- TODO: 需确认 -->` 注释标记
- Date Created 使用今天的日期
- Section 9.1（Core Requirements）直接保留标准需求，不做修改
- Section 10（Non-Functional Requirements）直接保留标准值，除非描述中有特殊要求
- Section 17 Appendix B（Related Documents）路径统一使用 `docs/` 前缀
- 如果我提供了样例 Excel 文件路径，先读取该文件以了解实际的列结构、分组方式和数据格式，用于准确填写 Section 4（Input Specification）和 Section 5（Split Modes）

## 我的项目描述

[在此粘贴你的项目描述]

## 样例 Excel 文件（如有）

[在此提供文件路径，例如：/项目名/samples/example.xlsx]
