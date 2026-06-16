# AI Resume Agent - 全链路求职战略家

**设计文档**

---

## 1. 概述

### 1.1 项目定位

面向AI产品经理求职者的智能简历优化系统，通过多Agent协作完成从JD分析到面试准备的完整链路。

### 1.2 核心价值

- **防幻觉设计**：用户确认机制确保AI不编造经历
- **多Agent协作**：展示对Agent系统的深度理解
- **可解释性**：每个修改都有清晰的Reason字段
- **迭代优化**：评分循环持续提升简历质量

---

## 2. 架构设计

### 2.1 Agent协作流

```
User Input → Analyst → Optimizer → Verifier → Recruiter → Output
                                ↑                      ↓
                                ←←←← 循环迭代 ←←←←
```

### 2.2 各Agent职责

| Agent | 名称 | 输入 | 输出 | 职责 |
|-------|------|------|------|------|
| A | Analyst | JD | JDAnalysis | 深度解码JD，识别显性/隐性需求 |
| B | Optimizer | 原始简历 + JD分析 | OptimizedResume | STAR法则重构，量化建议 |
| V | Verifier | 原始简历 + 优化简历 | QuantificationWarning[] | 高亮可疑指标，用户确认 |
| C | Recruiter | 优化简历 + JD分析 | ScoreReport + Questions | 生成面试题，评分报告 |

### 2.3 关键设计决策

#### 防幻觉机制

Verifier Agent是核心差异化设计：
- 对比原始vs优化简历
- 高亮所有新增量化指标
- **阻塞式确认**：用户不确认不继续
- 体现AIGC合规性思考

#### 循环退出机制

- Max_Retries = 3
- 每次迭代：Recruiter评分 → 反馈给Optimizer
- 动态提示工程：评分反馈作为下一次优化的Constraint

#### 两阶段实施

**Phase 1 (当前)**：JSON模板 + 规则基础分析
**Phase 2 (后期)**：ChromaDB向量检索 + AI增强分析

---

## 3. 数据模型

### 3.1 Pydantic Schema

```python
class JDAnalysis(BaseModel):
    core_skills: List[str]
    soft_skills: List[str]
    hidden_requirements: List[str]
    keyword_weights: Dict[str, float]
    industry_context: str

class OptimizationLogic(BaseModel):
    original_text: str
    optimized_text: str
    reason: str  # 可解释性
    jd_keyword_matched: str

class QuantificationWarning(BaseModel):
    original_claim: str
    suggested_claim: str
    basis: str
    user_confirmed: bool

class ScoreReport(BaseModel):
    overall_score: float
    dimensions: Dict[str, float]
    radar_chart_ascii: str
    feedback: str
    interview_readiness: str
```

---

## 4. 评分维度

| 维度 | 评估内容 | 权重 |
|------|----------|------|
| 逻辑性 | STAR法则使用 | 25% |
| 技术深度 | JD技能匹配 | 25% |
| 业务贡献 | 量化指标密度 | 25% |
| 排版美观 | 结构化程度 | 25% |

---

## 5. 输出格式

### 5.1 Markdown导出

- 优化后简历
- 修改日志（Optimization_Logic）
- 评分报告（含雷达图）
- 面试问题列表

### 5.2 ASCII雷达图

```
==================================================
           评 分 雷 达 图
==================================================
  逻辑性: ████████░░ 80.0
  技术深度: ██████░░░░ 60.0
  业务贡献: ███████░░░ 70.0
  排版美观: ████████░░ 80.0
==================================================

综合得分: 72.5
```

---

## 6. 扩展性设计

### 6.1 向量数据库预留

```python
# template_store.py
def upgrade_to_vector_db(self, path: str = None):
    """Phase 2: 从JSON升级到ChromaDB"""
    raise NotImplementedError
```

### 6.2 LLM客户端预留

当前使用规则基础分析，接口预留LLM客户端：

```python
class AnalystAgent:
    def __init__(self, llm_client=None):
        if llm_client:
            return await self._ai_analyze(jd_text)
        return self._rule_based_analyze(jd_text)
```

---

## 7. 技术选型

| 模块 | 方案 | 理由 |
|------|------|------|
| Agent框架 | 纯Python类 | 降低复杂度，便于面试讲解 |
| 数据验证 | Pydantic | 结构化输出，可视化友好 |
| 评分图表 | ASCII Art | 零依赖，终端友好 |
| 模板存储 | JSON (→ChromaDB) | Phase 1/2分离 |
| API客户端 | 预留接口 | 可接入GPT-4o/Gemini |

---

## 8. 面试亮点

1. **多Agent架构**：不是单一Prompt，而是分工协作的Agent系统
2. **防幻觉设计**：体现AIGC合规意识，这是面试官必问的点
3. **可解释性**：每个修改都有reason字段，展示Explainable AI思考
4. **迭代思维**：Phase 1/2分离，体现MVP和敏捷方法论
5. **评分闭环**：Recruiter评分 → 反馈Optimizer → 持续优化

---

*文档版本: 1.0*
*最后更新: 2026-04-22*