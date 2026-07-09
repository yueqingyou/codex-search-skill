# Intent Classification Guide

搜索意图分类的详细指南。Agent 在执行搜索前先判断用户查询意图，然后在同一个质量优先流程里调整 freshness、query bundle、source filter 和评分权重。

## 通用原则

- 顶层搜索行为只有一种：质量优先、多源并行、统一去重与评分。
- 默认尽可能调用所有已配置源：Grok、Exa、Tavily、OpenAlex。
- `--source` 只用于显式收窄源集合，例如只测 Grok 或只查论文图谱。
- `--queries` 用于小规模查询扩展，不要为了看起来全面而制造大量低价值子查询。
- 重要结论必须回到源页面、官方文档、论文页面或原始讨论验证。

## 七种意图类型

### 1. Factual（事实查询）

**识别信号**：
- "什么是 X"、"X 的定义"、"X 是什么意思"
- "What is X"、"Define X"、"X meaning"
- 问句结构，期望一个明确答案

**搜索策略**：
- Freshness: 不限，除非用户问的是当前状态。
- 查询扩展: 加 "definition"、"explained"、"overview"。
- 结果偏好: 权威文档 > 百科 > 社区解答。

**权重配置**：`--intent factual`

```text
keyword_match: 0.4, freshness: 0.1, authority: 0.5
```

### 2. Status（状态/进展查询）

**识别信号**：
- "X 最新进展"、"X 现在怎样了"、"X 的状态"
- "X latest"、"X update"、"What's new with X"
- 含时间暗示词：最新、最近、目前、现在、进展

**搜索策略**：
- Freshness: `pw`（过去一周）或 `pm`（过去一月）。
- 查询扩展: 加当前年份、"latest"、"update"、"release"。
- 结果偏好: 最新 > 权威 > 完整。

**权重配置**：`--intent status`

```text
keyword_match: 0.3, freshness: 0.5, authority: 0.2
```

### 3. Comparison（对比查询）

**识别信号**：
- "X vs Y"、"X 和 Y 的区别"、"X 还是 Y"
- "X compared to Y"、"X or Y"、"difference between X and Y"
- 两个或多个实体的并列

**搜索策略**：
- Freshness: 通常用 `py`，确保评测和生态判断不过时。
- 查询分解: 生成 3 个子查询。
- 查询示例: `"X vs Y"`, `"X advantages features"`, `"Y advantages features"`。
- 结果偏好: 同时包含两者的文章 > 单方面评测。

**权重配置**：`--intent comparison`

```text
keyword_match: 0.4, freshness: 0.2, authority: 0.4
```

### 4. Tutorial（教程/操作指南）

**识别信号**：
- "怎么做 X"、"如何 X"、"X 教程"、"X 入门"
- "How to X"、"X tutorial"、"X guide"、"getting started with X"
- 动作导向的问句

**搜索策略**：
- Freshness: 常用 `py`，避免过时教程。
- 查询扩展: 加 "tutorial"、"guide"、"step by step"、"example"。
- Domain boost: `dev.to,freecodecamp.org,realpython.com,baeldung.com`。
- 结果偏好: 步骤清晰的教程 > 概念解释。

**权重配置**：`--intent tutorial`

```text
keyword_match: 0.4, freshness: 0.1, authority: 0.5
```

### 5. Exploratory（探索性查询）

**识别信号**：
- "关于 X 的一切"、"全面了解 X"、"X 生态"
- "Everything about X"、"X ecosystem"、"X dive"
- 开放式、无明确边界的查询

**搜索策略**：
- Freshness: 可选；若涉及当下生态或推荐，使用 `py` 或 `pm`。
- 查询分解: 生成 2-3 个角度。
- 查询示例: `"X overview architecture"`, `"X ecosystem community"`, `"X use cases applications"`。
- 结果偏好: 覆盖面广 > 单点详尽。

**权重配置**：`--intent exploratory`

```text
keyword_match: 0.3, freshness: 0.2, authority: 0.5
```

### 6. News（新闻查询）

**识别信号**：
- "X 新闻"、"X 最近发生了什么"、"本周 X"
- "X news"、"X this week"、"latest X announcements"
- 明确的新闻/时事导向

**搜索策略**：
- Freshness: `pd`（24h）或 `pw`（一周）。
- 查询扩展: 加 "news"、"announcement"、"release"、当前日期。
- 结果偏好: 最新 > 一切，同时必须核对发布日期。

**权重配置**：`--intent news`

```text
keyword_match: 0.3, freshness: 0.6, authority: 0.1
```

### 7. Resource（资源定位）

**识别信号**：
- "X 官网"、"X GitHub"、"X 文档"、"X 下载"
- "X official site"、"X documentation"、"X repo"
- 寻找特定资源/链接

**搜索策略**：
- Freshness: 不限。
- 查询扩展: 加 "official"、"github"、"documentation" 等具体资源类型。
- Source filter: 如果只要官方入口，可优先跑 `--source grok,exa,tavily`，但默认全源也可以。
- 结果偏好: 精确匹配 > 相关内容。

**权重配置**：`--intent resource`

```text
keyword_match: 0.5, freshness: 0.1, authority: 0.4
```

## 意图判断流程

```text
1. 扫描查询中的信号词。
2. 如果匹配多个类型，按优先级选择：Resource > News > Status > Comparison > Tutorial > Factual > Exploratory。
3. 如果无法判断，默认 exploratory。
4. 中文技术查询同时生成英文变体。
```

示例：

- `"Deno 最新版本下载"` 同时匹配 Status 和 Resource，选择 Resource。
- `"Bun vs Deno 最新对比"` 同时匹配 Comparison 和 Status，选择 Comparison 并使用 freshness。

## 查询扩展规则

### 技术同义词

- k8s -> Kubernetes
- JS -> JavaScript
- TS -> TypeScript
- React -> React.js / ReactJS
- Vue -> Vue.js / VueJS
- Go -> Golang
- Postgres -> PostgreSQL
- Mongo -> MongoDB
- tf -> TensorFlow
- torch -> PyTorch

### 语言适配

- 中文技术查询同时搜英文版本。
- 例：`Rust 异步编程` -> `Rust async programming`。
