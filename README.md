# AI 简历优化 Agent

一个面向 AI 产品经理求职场景的多 Agent 简历优化系统。项目通过岗位 JD 分析、简历成稿优化、真实性风险校验、评分报告和模拟面试题生成，帮助用户把原始经历整理成更可信、更接近投递标准的简历版本。

## 核心功能

- **JD 深度分析**：识别岗位中的硬技能、软技能、隐性要求、行业背景、工具链和常见挑战。
- **简历成稿优化**：基于 STAR 法则重构经历，但严格保持用户真实经历边界。
- **防幻觉校验**：检测新增数字、职责升级、工具栈新增和公司级影响表述，避免 AI 编造或夸大。
- **补充信息清单**：当缺少真实数据、职责边界或工具证据时，输出待用户补充的问题。
- **多模型可切换**：支持 MiniMax、OpenAI、Gemini；未配置 API Key 时自动降级到规则模式。
- **评分报告**：从 JD 匹配、真实性风险、STAR 完整度、可读性、可投递度五个维度评分。
- **模拟面试题**：根据 JD 和优化后简历生成针对性面试问题。
- **网页前端**：支持粘贴文本或上传 PDF、Word、TXT，展示优化结果并下载 Word 报告。

## 项目结构

```text
ai-resume-agent/
├── api_server.py              # FastAPI 后端入口
├── main.py                    # 命令行入口
├── app_config.py              # 全局配置
├── agents/
│   ├── analyst.py             # JD 分析 Agent
│   ├── optimizer.py           # 简历优化 Agent
│   ├── verifier.py            # 真实性校验 Agent
│   └── recruiter.py           # 模拟面试与评分 Agent
├── services/
│   ├── llm_client.py          # 统一多模型客户端
│   ├── minimax_client.py      # MiniMax API 客户端
│   ├── evaluator.py           # 评分与改进建议
│   └── template_store.py      # 行业模板库
├── models/
│   └── schema.py              # Pydantic 数据模型
├── frontend/
│   └── index.html             # 单页前端
├── utils/
│   ├── markdown_exporter.py   # Markdown 报告导出
│   ├── word_exporter.py       # Word 报告导出
│   └── ascii_chart.py         # ASCII 雷达图
└── tests/
    └── test_quality_improvements.py
```

## 安装依赖

建议使用 Python 3.10 及以上版本。

```bash
pip install -r requirements.txt
```

## 模型配置

项目通过环境变量选择模型服务：

```bash
# 可选：minimax / openai / gemini
set LLM_PROVIDER=minimax

# 可选：覆盖默认模型
set LLM_MODEL=MiniMax-M2.7

# 按选择的 provider 配置对应 Key
set MINIMAX_API_KEY=your_minimax_key
set OPENAI_API_KEY=your_openai_key
set GEMINI_API_KEY=your_gemini_key
```

如果没有配置任何 API Key，系统会进入 `rule_based` 规则模式。规则模式可以演示流程和发现缺口，但不建议把输出直接作为最终投递简历。

## 启动网页服务

```bash
python api_server.py
```

默认访问：

```text
http://localhost:8000
```

如果 8000 端口被占用，也可以手动指定端口：

```bash
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001
```

Windows 用户也可以双击：

```text
启动前端.bat
```

## 命令行运行

```bash
python main.py
```

程序会提示输入目标 JD、原始简历和公司名称。直接回车可使用内置示例数据。

## API 接口

### 查看服务信息

```http
GET /api
```

### 优化简历

```http
POST /api/optimize
```

请求示例：

```json
{
  "job_description": "目标岗位 JD",
  "original_resume": "原始简历文本",
  "company_name": "目标公司名称"
}
```

响应会包含：

- `quality_mode`：`llm` 或 `rule_based`
- `jd_analysis`：JD 分析结果
- `optimized_resume`：优化后的简历文本和匹配分
- `missing_info_questions`：需要用户补充的信息
- `quantification_warnings`：需要确认的真实性风险
- `score_report`：评分报告
- `interview_questions`：模拟面试问题
- `modifications`：修改记录

### 上传文件解析

```http
POST /api/upload
```

支持 PDF、Word、TXT。

### 下载 Word 报告

```http
GET /api/download/word
```

前端会在用户确认风险项后调用该接口，尽量避免把未确认内容导出到最终 Word 文档。

## 质量控制设计

本项目的重点不是“把简历写得越夸张越好”，而是让 AI 在真实边界内提升表达质量。

系统会重点拦截以下风险：

- 原文没有数字，优化后出现百分比、人数、用户规模等具体数字。
- 原文是“参与/协助”，优化后变成“主导/牵头/负责人”。
- 原文没有工具栈证据，优化后新增 LangChain、RAG、SQL、Python 等能力。
- 原文没有影响范围，优化后出现“公司级/平台级/行业领先”等表述。

存在未确认风险或 `[需补充: ...]` 时，评分会被限制，避免产生虚高分。

## 测试

```bash
python -m pytest tests -q
```

当前测试覆盖：

- 弱动词替换不会产生重复文本。
- “参与”不会被自动升级为“主导”。
- 新增数字、工具栈、职责升级会被 Verifier 标记。
- 未配置 API Key 时进入 `rule_based` 模式。
- 不完整简历不会被评成虚高分。

## 后续可优化方向

- 将风险确认状态持久化到后端，而不是只保存在前端页面状态中。
- 给 OpenAI/Gemini 增加更严格的结构化输出校验和重试。
- 引入更丰富的行业模板库或向量检索。
- 增加端到端浏览器测试，覆盖上传、优化、确认、下载完整流程。

## License

MIT
