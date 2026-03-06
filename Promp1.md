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

这个项目用于切分一个formacion 评估的excel汇总文件。需要根据汇总的excel文件以Tutor列为拆分依据，将文件拆分成若干个文件，然后将文件作为附件随同邮件发送给每一位tutor。其中excel表格中的第一行到第三行都是抬头，第二行中是分类，而第二行下方相对应囊括的第三行是子类。因此APP需要具备只能识别变量标签的能力。在用户导入excel后，需要能够根据tutor拆分，同时会以某一个tutor的数据作为范例，引导用户选择在拆分文件中需要出现的列数。拆分后的每个excel 需要保留抬头以及相应的数据并且所有的格式都必须得到保留，包括颜色，字体，每个单元格的宽度高度，以及填充的样式等一系列都必须保持原状。并且在，邮件内容的预设中允许用户拆入图片以及其他高级的排版功能，并且在转发邮件时能够保留这一系列的设计排版。

## 样例 Excel 文件（如有）

/项目名/Ejemplo/2025-Notas evaluaciones Auditoria_Gerente y Socios.xlsx
