```
██████╗ ██████╗ ██╗███████╗███╗   ███╗
██╔══██╗██╔══██╗██║██╔════╝████╗ ████║
██████╔╝██████╔╝██║███████╗██╔████╔██║
██╔═══╝ ██╔══██╗██║╚════██║██║╚██╔╝██║
██║     ██║  ██║██║███████║██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝
```

# PRISM — Code Quality Metrics Platform

Multi-agent code quality analysis platform deploying 10 specialized AI agents for comprehensive codebase quality assessment.

## Architecture

```
Codebase → [Pipeline] → Report
    ├─ Complexity Analyzer (16K tok)
    ├─ Maintainability Scorer (14K tok)
    ├─ Code Smell Detector (18K tok)
    ├─ Naming Convention Checker (12K tok)
    ├─ Duplication Finder (20K tok)
    ├─ Style Compliance (12K tok)
    ├─ Documentation Coverage (14K tok)
    ├─ Test Coverage Analyzer (16K tok)
    ├─ Coupling Analyzer (18K tok)
    └─ Quality Gate (15K tok)
```

## Token Consumption

| Agent | Tokens/Scan | Scans/Day | Daily Total |
|-------|-------------|-----------|-------------|
| Complexity Analyzer | 16K | 700 | 11.2M |
| Duplication Finder | 20K | 500 | 10.0M |
| Code Smell Detector | 18K | 500 | 9.0M |
| Coupling Analyzer | 18K | 450 | 8.1M |
| Quality Gate | 15K | 500 | 7.5M |
| Test Coverage | 16K | 400 | 6.4M |
| Maintainability | 14K | 400 | 5.6M |
| Documentation | 14K | 350 | 4.9M |
| Style Compliance | 12K | 350 | 4.2M |
| Naming Checker | 12K | 300 | 3.6M |
| **Total** | **155K** | | **70.5M/day** |

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

## Usage

```bash
# CLI
python cli.py analyze ./src
python cli.py agents
python cli.py stats

# Web Dashboard
python web/app.py  # http://localhost:8081
```

## Agents

1. **Complexity Analyzer** — Cyclomatic/cognitive complexity, nesting depth analysis
2. **Maintainability Scorer** — Maintainability index, technical debt ratio
3. **Code Smell Detector** — God class, long method, feature envy, data clumps
4. **Naming Convention Checker** — Naming patterns, consistency, readability
5. **Duplication Finder** — Copy-paste detection, similar blocks, DRY violations
6. **Style Compliance** — PEP8/ESLint rules, formatting, line length
7. **Documentation Coverage** — Docstring coverage, comment density, API docs
8. **Test Coverage Analyzer** — Test patterns, assertion quality, edge cases
9. **Coupling Analyzer** — Afferent/efferent coupling, instability, abstractness
10. **Quality Gate** — Pass/fail scoring, thresholds, trend analysis

## License

MIT
