# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AI Resume Agent is a multi-Agent resume optimization system designed as an AI PM portfolio project. It demonstrates understanding of Agent systems, AIGC compliance, and iterative design through a 4-Agent architecture.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run backend API server (recommended)
python api_server.py

# Run frontend (after starting API server, open in browser)
cd frontend && start index.html
# Or open directly via API server at http://localhost:8000

# Run backend (CLI mode - legacy)
set PYTHONIOENCODING=utf-8 && python -X utf8 main.py

# Configure API keys (optional, runs in mock mode without)
export OPENAI_API_KEY="your-key"
export GEMINI_API_KEY="your-key"
```

## API Server

FastAPI-based REST API server at `api_server.py`:
- `POST /api/optimize` - Main resume optimization endpoint
- `GET /` - Serves frontend HTML
- `GET /docs` - Swagger API documentation

## Architecture

**4-Agent Pipeline:**
```
User Input → Analyst → Optimizer → Verifier → Recruiter → Output
                            ↑                      ↓
                            ←←← 循环迭代 (≤3次) ←←←
```

- **Analyst (A)**: Decodes JD, extracts keywords/hidden requirements
- **Optimizer (B)**: STAR-method restructuring, quantification suggestions
- **Verifier (V)**: Anti-hallucination check - highlights new metrics, blocks for user confirmation
- **Recruiter (C)**: Generates interview questions, produces score report

**Key Design Decisions:**

1. **Anti-hallucination mechanism** - Verifier compares original vs optimized resume, highlights quantified claims, requires user confirmation before proceeding
2. **Iteration loop** - Max 3 retries, Recruiter scores → feedback to Optimizer → dynamic prompt engineering
3. **Phase 1/2 separation** - Phase 1 uses JSON templates, Phase 2 (future) upgrades to ChromaDB vector search
4. **Explainability** - Every optimization includes `reason` field explaining why the change was made

## Data Models

Pydantic schemas in `models/schema.py`:
- `JDAnalysis`: core_skills, soft_skills, hidden_requirements, keyword_weights
- `OptimizedResume`: sections + optimization_logics[] with reason field
- `QuantificationWarning`: original_claim, suggested_claim, basis, user_confirmed
- `ScoreReport`: overall_score, dimensions, radar_chart_ascii, feedback

## Configuration

In `app_config.py`:
- `MAX_RETRIES = 3` - prevents infinite loops
- `MATCH_SCORE_THRESHOLD = 75.0` - triggers optimization loop when below
- Supports OpenAI (gpt-4o) and Gemini API keys via environment variables

## Scoring Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| 逻辑性 | 25% | STAR method usage |
| 技术深度 | 25% | JD skill matching |
| 业务贡献 | 25% | Quantification density |
| 排版美观 | 25% | Structure score |

## Interview Talking Points

This project is designed as a portfolio piece. Key highlights:
1. Multi-Agent collaboration (not single prompt)
2. Verifier as anti-hallucination differentiator
3. Optimization_Logic field for AI explainability
4. Phase 1/2 separation showing iterative thinking
