# paper-extract

## 描述

从论文 PDF 中自动提取元信息和结构化内容，写入飞书多维表格。支持建筑学/城乡规划等领域论文的全维度 AI 提取，可与组会研究追踪系统联动。

## 首次使用：研究背景配置

**初次使用时，我会询问你的研究背景，用于驱动后续的论文相关性判断和借鉴分析。**

配置内容包括：
- 论文题目（或方向）
- 核心研究问题
- 研究方法框架
- 理论基础
- 研究范围（地域/案例）
- 关键概念

配置后保存为 `.paper-extract-config.json`，后续使用无需重复配置。如需更新背景，说"更新研究背景"即可。

## 触发方式

**触发词**：`/paper-extract`、`开始总结论文`、`提取论文`

```
/paper-extract <record_id>     # 处理指定记录
/paper-extract --all            # 处理所有未提取的记录
开始总结论文                     # 同上，处理最新上传的未提取论文
```

## 前置条件

- 飞书 CLI (`lark-cli`) 已安装并登录
- Python 3 + pdfplumber + PyMuPDF 已安装
- 飞书多维表格已创建（字段方案见下方）
- 可选：Anthropic API Key（用于独立的 API 调用；也可由 Claude Code 内置能力驱动）

## 飞书表格字段方案

### 元信息字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| PDF附件 | 附件 | 上传论文 PDF |
| 论文标题 | 文本 | AI 提取 |
| 作者 | 文本 | AI 提取 |
| 年份 | 数字 | AI 提取 |
| 期刊/来源 | 文本 | AI 提取 |
| 学校 | 文本 | AI 提取 |
| 关键词 | 多选 | AI 提取 |

### 内容提取字段（标签 + 详情 配对）

| 标签字段(多选) | 详情字段(多行文本) | 提取内容 |
|---------------|-------------------|---------|
| 背景标签 | 背景详情 | 研究背景与问题 |
| 国内综述标签 | 国内综述详情 | 国内研究现状 |
| 国际综述标签 | 国际综述详情 | 国外研究现状 |
| 政策标签 | 政策详情 | 政策/规划文件 |
| 方法标签 | 方法详情 | 研究方法、数据来源、技术路线 |
| 结论标签 | 结论详情 | 核心发现与结论 |
| 引用标签 | 引用详情 | 可直接引用的原文段落 |

### 深度分析字段

| 字段名 | 类型 | 对应分析维度 |
|--------|------|-------------|
| 核心问题 | 多行文本 | 核心研究问题 + 子问题链（鱼头） |
| 方法论贡献 | 多行文本 | 方法论层面的独特贡献 |
| 优点 | 多行文本 | 逻辑/方法/写作三个层面的可借鉴之处 |
| 不足 | 多行文本 | 方法论/逻辑/表述/实操四类缺陷 |
| 对我论文的借鉴 | 多行文本 | 直接迁移/调整后用/注意避坑 |
| 理论标签 | 多选 | 论文涉及的理论 |
| 理论详情 | 多行文本 | 理论框架详解 |

### 手动字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 相关度 | 单选 | ⭐1-5 与研究的相关程度 |
| 我的笔记 | 多行文本 | 自由笔记，可关联知识库精读笔记链接 |

---

## 工作流

### Step 0: 首次配置检查

检查是否存在 `.paper-extract-config.json`。若不存在，询问用户研究背景并保存配置。

### Step 1: 定位目标记录

**如果用户指定了 `<record_id>`：**
```bash
lark-cli base +record-get --base-token <BASE_TOKEN> \
  --table-id <TABLE_ID> --record-id <record_id> --as user
```

**如果用户指定了 `--all`：**
查找 PDF附件字段不为空、但论文标题字段为空的记录：
```bash
lark-cli base +record-list --base-token <BASE_TOKEN> \
  --table-id <TABLE_ID> --as user --format json
```

### Step 2: 下载 PDF 附件

```bash
lark-cli base +record-download-attachment --base-token <BASE_TOKEN> \
  --table-id <TABLE_ID> --record-id <record_id> \
  --file-token <FILE_TOKEN> --output ./data/papers/<record_id>.pdf --as user
```

### Step 3: 提取 PDF 文本（三级降级策略）

**第一级：pdfplumber（主力）**
```bash
python3 scripts/pdf_extract.py ./data/papers/<record_id>.pdf --core-only
```

**第二级：PyMuPDF/fitz（兼容性更好）**
pdfplumber 对某些 PDF 内部结构兼容性差（如 Unexpected EOF 错误），用 PyMuPDF 重试：
```bash
python3 -c "
import fitz
doc = fitz.open('./data/papers/<record_id>.pdf')
text = ''
for page in doc:
    text += page.get_text()
with open('./data/papers/<record_id>_fitz.txt', 'w') as f:
    f.write(text)
doc.close()
"
```

**第三级：OCR skill（扫描版/图片型 PDF）**
调用 `pdf-ocr-extraction` skill 进行 OCR 文字识别。

如果是硕博论文（>50页），优先使用 `--core-only` 只提取核心章节。
如果是期刊论文（<30页），提取全文。

### Step 4: AI 提取

#### 4a: 先读取现有标签选项

在提取前，获取所有多选字段的已有选项，供 AI 做同义词去重：
```bash
lark-cli base +field-list --base-token <BASE_TOKEN> --table-id <TABLE_ID> --as user
```

#### 4b: Round 1 — 元信息提取

将 PDF 提取文本的开头部分（约前5000字）发给 AI 提取元信息。
输出：论文标题、作者、年份、期刊/来源、学校、关键词。

#### 4c: Round 2 — 内容维度提取（鱼头-鱼身-鱼尾框架）

提取框架来自导师论文阅读方法论：
- **鱼头**：核心研究问题 + 子问题链
- **鱼身**：研究方法（数据来源/样本量/技术路线/案例选择）
- **鱼尾**：核心结论（严格区分「现状描述」vs「研究结论」）

**关键质量红线**（来自导师方法论，注入每次提取）：
1. ❌ 混淆研究目标与核心问题——「研究了什么」≠「解决了什么根本痛点」
2. ❌ 把背景信息当成结论——现象描述和数据罗列不是研究贡献
3. ❌ 标签化表述——不能说「设施不足」，要说「缺什么、缺多少、为什么缺」
4. ❌ 跳过分析直接给结论——还原完整的提问→分析→解决逻辑链
5. ❌ 只会复述不会判断——必须明确说「哪里好、为什么好」「哪里有问题、什么问题」
6. ❌ 为复杂方法喝彩——工具复杂≠有价值，要问「这个方法得出了什么有意义的洞见」
7. ❌ 脱离用户论文泛泛而读——每一处分析都要问「这对我有什么用」

提取 14 个内容维度：核心问题、背景（标签+详情）、国内综述、国际综述、政策、方法、结论、方法论贡献、优点、不足、对我论文的借鉴、理论（标签+详情）、引用。

**同义词规则**：标签创建前检查已有选项。同义词必须复用已有标签（如 POE=使用后评价，城市更新=旧城改造）。不确定时创建新标签。中文/英文/缩写统一使用中文全称。

### Step 5: 写入飞书表格

#### 5a: Round 1 元信息写入
```bash
lark-cli base +record-upsert --base-token <BASE_TOKEN> \
  --table-id <TABLE_ID> --record-id <record_id> \
  --json '{"论文标题":"...","作者":"...","年份":...,...}' --as user
```

#### 5b: Round 2 内容维度写入
```bash
lark-cli base +record-upsert --base-token <BASE_TOKEN> \
  --table-id <TABLE_ID> --record-id <record_id> \
  --json '{"核心问题":"...","背景标签":[...],"背景详情":"...",...}' --as user
```

---

## 与组会研究追踪系统联动

如果你的研究使用了组会纪要追踪系统（如 Academic/组会知识库），paper-extract 可以：

1. **论文-组会关联**：提取论文后，将论文信息与对应日期的组会纪要关联
2. **研究基因图谱更新**：提取的方法论贡献可补充你的方法论DNA追踪
3. **TODO 关联**：论文中发现的待研究问题可添加到 TODO 追踪列表
4. **概念流动追踪**：论文中的关键概念可补充到概念流动图中

联动数据格式参考 `linkage_data.json`。

---

## 降级策略

| 级别 | 工具 | 适用场景 |
|------|------|---------|
| 1 | pdfplumber | 标准 PDF，文字层完好 |
| 2 | PyMuPDF/fitz | PDF 结构异常但文字层存在 |
| 3 | pdf-ocr-extraction skill | 扫描版/图片型 PDF |

## 失败处理

- **PDF 三级降级全部失败**：在笔记字段标注"⚠️ PDF无法提取文字"，告知用户
- **某维度无内容**：标签字段写空数组 `[]`，详情字段写 `"(无相关内容)"`
- **提取中断**：重新运行时自动跳过已填字段（断点续传）

## 依赖清单

```
# Python 依赖
pdfplumber>=0.10.0
PyMuPDF>=1.24.0

# 系统依赖
lark-cli (飞书官方 CLI)
```

## 致谢

论文阅读方法论提炼自导师组会的反馈建议，在此致谢。

## License

MIT
