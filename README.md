# Paper Extract — 论文 AI 提取助手

> 上传 PDF → AI 自动提取 20+ 结构化维度 → 写入飞书多维表格

让论文阅读从"翻 PDF + 手动笔记"变成"上传即提取、表格化管理、跨论文综合分析"。专为学术论文阅读场景设计，内置导师论文阅读方法论（鱼头-鱼身-鱼尾框架）。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blue)](https://claude.ai/code)

---

## 目录

- [核心功能](#核心功能)
- [快速开始](#快速开始)
- [Skill 安装](#skill-安装)
- [飞书表格字段方案](#飞书表格字段方案)
- [技术架构](#技术架构)
- [PDF 三级降级策略](#pdf-三级降级策略)
- [与组会研究追踪联动](#与组会研究追踪联动)
- [项目结构](#项目结构)
- [致谢](#致谢)

---

## 核心功能

- **一张表管理所有论文**：飞书多维表格存储，支持字段筛选、多选标签、全文检索
- **AI 全维度提取**：上传 PDF 后自动提取元信息 + 17 个内容维度（标签+详情+深度分析），含导师论文阅读方法论框架
- **标签化 + 详情化双字段**：每个维度配有标签（多选，快速筛选）和详情（Markdown，深入阅读）
- **首次使用智能配置**：初次运行询问你的研究背景，后续自动用于论文相关性判断和借鉴分析
- **同义词自动去重**：标签创建时智能复用已有选项，"POE"和"使用后评价"不会并存
- **断点续传**：提取中断后重跑自动跳过已完成字段
- **三级 PDF 降级**：pdfplumber → PyMuPDF → OCR skill，兼容各种 PDF 格式
- **组会系统联动**：可与组会研究追踪系统联动，补充方法论DNA和概念流动

---

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 22+（飞书 CLI 依赖）
- 飞书开放平台应用（需 Base、Drive 权限）
- Claude Code（推荐）或 Anthropic API Key

### 2. 安装依赖

```bash
# Python PDF 处理
pip install pdfplumber PyMuPDF python-dotenv

# 飞书 CLI
npm install -g @larksuite/cli
npx skills add larksuite/cli -y -g
```

### 3. 配置飞书 CLI

```bash
lark-cli config init --app-id <your_app_id> --app-secret-stdin
lark-cli auth login --recommend
```

### 4. 创建飞书多维表格

使用 `lark-cli base +base-create` 创建 Base，按下方字段方案建表。或直接复制[模板表格](#)。

### 5. 安装 Skill

```bash
# 从本项目安装公开版 skill
cp .claude/skills/paper-extract-public.md ~/.claude/skills/paper-extract.md
```

### 6. 使用

1. 在飞书表格中上传论文 PDF 到"PDF附件"字段
2. 在 Claude Code 中说：

```
/paper-extract <record_id>    # 处理指定记录
开始总结论文                    # 处理最新未提取的论文
```

**首次运行时**，AI 会询问你的研究背景（题目、核心问题、方法框架、研究范围等），保存配置后自动用于后续所有论文的借鉴分析。

---

## Skill 安装

### 方式一：从 GitHub 直接复制

```bash
git clone https://github.com/Che727/paper-extract.git
cp paper-extract/.claude/skills/paper-extract-public.md ~/.claude/skills/paper-extract.md
```

### 方式二：通过 Skills CLI（待上架）

```bash
npx skills add Che727/paper-extract@paper-extract-public -g -y
```

---

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
| 关键词 | 多选 | AI 提取，含同义词去重 |

### 内容提取字段（标签 + 详情 配对）

| 标签字段(多选) | 详情字段(多行文本) | 提取内容 |
|---------------|-------------------|---------|
| 背景标签 | 背景详情 | 研究背景与问题 |
| 国内综述标签 | 国内综述详情 | 国内研究现状、主要学者/团队 |
| 国际综述标签 | 国际综述详情 | 国外研究现状、国际理论 |
| 政策标签 | 政策详情 | 政策文件、规划文件、法规 |
| 方法标签 | 方法详情 | 研究设计、数据来源、样本量、分析工具、技术路线 |
| 结论标签 | 结论详情 | 核心发现，区分现状vs结论 |
| 引用标签 | 引用详情 | 可直接引用的原文段落（含页码） |

### 深度分析字段

| 字段名 | 类型 | 对应分析维度 |
|--------|------|-------------|
| 核心问题 | 多行文本 | 🎯 根本痛点 + 子问题链（鱼头） |
| 方法论贡献 | 多行文本 | 🧬 新框架？改进方法？新数据源？新视角？ |
| 优点 | 多行文本 | ✅ 逻辑/方法/写作 三个层面的具体优点 |
| 不足 | 多行文本 | ❌ 方法论/逻辑/表述/实操 四类缺陷 |
| 对我论文的借鉴 | 多行文本 | 🔗 直接迁移 / 调整后用 / 注意避坑 |
| 理论标签 | 多选 | 📚 论文涉及的理论 |
| 理论详情 | 多行文本 | 📚 理论的提出者、核心概念、应用方式 |

### 手动字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 相关度 | 单选 | ⭐1-5 与研究的相关程度（AI 自动预填） |
| 我的笔记 | 多行文本 | 自由笔记，可存知识库精读笔记链接 |

---

## 技术架构

```
论文 PDF
  │
  ├── 三级降级提取文本
  │   ├── 1️⃣ pdfplumber（标准 PDF）
  │   ├── 2️⃣ PyMuPDF/fitz（结构异常 PDF，如 Unexpected EOF）
  │   └── 3️⃣ pdf-ocr-extraction skill（扫描版/图片型 PDF）
  │
  ├── Claude AI 两轮提取（Round 1 元信息 + Round 2 内容维度）
  │   ├── 系统提示注入用户研究背景（首次配置）
  │   ├── 鱼头-鱼身-鱼尾 论文阅读框架
  │   ├── 8 条质量红线（区分目标vs问题、现状vs结论…）
  │   ├── 标签去重：先读已有选项 → 同义词判定 → 复用或新建
  │   └── 输出：17 个内容维度 + 7 组标签/详情配对
  │
  └── lark-cli 写入飞书多维表格
      ├── Round 1 结果 → 元信息字段
      └── Round 2 结果 → 内容维度字段
```

---

## PDF 三级降级策略

并非所有 PDF 都能被 pdfplumber 正常解析。本系统设计了三级降级：

| 级别 | 工具 | 适用场景 | 成功率 |
|------|------|---------|--------|
| **1** | pdfplumber | 标准 PDF，文字层完好 | 90%+ |
| **2** | PyMuPDF (fitz) | PDF 结构异常但文字层存在（Unexpected EOF 等） | 8% |
| **3** | pdf-ocr-extraction skill | 扫描版/图片型 PDF，无文字层 | 2% |

硕博论文（>50页）自动提取核心章节（摘要→绪论→方法→实证→结论），跳过中间章节，节省 token。

---

## 与组会研究追踪联动

如果你的研究使用组会纪要追踪系统，paper-extract 可以：

| 联动功能 | 说明 |
|----------|------|
| **论文-组会关联** | 提取的论文信息与对应日期组会纪要关联 |
| **方法论DNA更新** | 论文的方法论贡献补充到研究基因图谱 |
| **TODO 关联** | 论文中的待研究问题添加到追踪列表 |
| **概念流动** | 论文关键概念补充到概念流动图 |

---

## 项目结构

```
paper-extract/
├── .claude/skills/
│   ├── paper-extract.md              # Skill 本地版（含个人研究背景）
│   └── paper-extract-public.md       # Skill 公开版（首次配置引导，可分享）
├── scripts/
│   └── pdf_extract.py                # PDF 文本提取脚本
├── data/papers/                      # PDF 暂存目录（.gitignore）
├── requirements.txt                  # Python 依赖
├── .env.example                      # API Key 模板
├── .gitignore
└── README.md
```

> **注意**：`paper-extract.md`（本地版）包含个人研究背景，已加入 `.gitignore`，不会上传 GitHub。
> 如需分享，使用 `paper-extract-public.md`（公开版），安装后首次运行会询问研究背景。

---

## 致谢

本项目论文阅读方法论（鱼头-鱼身-鱼尾框架 + 8 条质量红线）提炼自导师组会的反馈建议，在此致谢。

## License

MIT © Che727
