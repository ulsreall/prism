# PRISM Architecture

## Pipeline Flow

```
Input Code
    │
    ▼
┌─────────────────┐
│ Complexity       │ 16K tokens
│ Analyzer         │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Maintainability  │ 14K tokens
│ Scorer           │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Code Smell       │ 18K tokens
│ Detector         │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Naming           │ 12K tokens
│ Convention       │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Duplication      │ 20K tokens
│ Finder           │
└────────┬────────┘
         ▼
... (5 more agents)
         ▼
┌─────────────────┐
│ Quality Gate     │ 15K tokens
│ (Final Score)    │
└────────┬────────┘
         ▼
    Quality Report
```

## Token Model

- Per-analysis: ~155K tokens (all 10 agents)
- Daily: ~68M tokens (700 analyses)
- Monthly: ~2.04B tokens
- MiMo 1.6B plan required
