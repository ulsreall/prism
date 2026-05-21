"""
PRISM Configuration Module
Central configuration for all agents and platform settings.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for individual analysis agents."""
    name: str
    weight: float
    daily_token_budget: int
    description: str
    enabled: bool = True


@dataclass
class PlatformConfig:
    """Main platform configuration."""
    daily_token_budget: int = int(os.getenv("DAILY_TOKEN_BUDGET", 68_000_000))
    monthly_token_budget: int = int(os.getenv("MONTHLY_TOKEN_BUDGET", 1_600_000_000))
    max_file_size_kb: int = int(os.getenv("MAX_FILE_SIZE_KB", 500))
    max_concurrent_agents: int = int(os.getenv("MAX_CONCURRENT_AGENTS", 10))
    analysis_timeout: int = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", 300))
    secret_key: str = os.getenv("SECRET_KEY", "prism-dev-key-change-in-production")
    flask_port: int = int(os.getenv("FLASK_PORT", 8081))

    # Quality thresholds
    quality_gate_threshold: float = 70.0
    complexity_threshold: int = 10
    duplication_threshold: float = 5.0
    coverage_threshold: float = 80.0


AGENT_CONFIGS: List[AgentConfig] = [
    AgentConfig(
        name="Complexity Analyzer",
        weight=float(os.getenv("COMPLEXITY_WEIGHT", 15)),
        daily_token_budget=7_500_000,
        description="Analyzes cyclomatic/cognitive complexity and nesting depth"
    ),
    AgentConfig(
        name="Maintainability Scorer",
        weight=float(os.getenv("MAINTAINABILITY_WEIGHT", 12)),
        daily_token_budget=6_000_000,
        description="Calculates maintainability index and technical debt ratio"
    ),
    AgentConfig(
        name="Code Smell Detector",
        weight=float(os.getenv("CODE_SMELL_WEIGHT", 18)),
        daily_token_budget=9_000_000,
        description="Detects god classes, long methods, feature envy, data clumps"
    ),
    AgentConfig(
        name="Naming Convention Checker",
        weight=float(os.getenv("NAMING_WEIGHT", 10)),
        daily_token_budget=5_000_000,
        description="Checks naming patterns, consistency, and readability"
    ),
    AgentConfig(
        name="Duplication Finder",
        weight=float(os.getenv("DUPLICATION_WEIGHT", 20)),
        daily_token_budget=10_000_000,
        description="Finds copy-paste code, similar blocks, DRY violations"
    ),
    AgentConfig(
        name="Style Compliance",
        weight=float(os.getenv("STYLE_WEIGHT", 10)),
        daily_token_budget=5_000_000,
        description="Checks PEP8/ESLint rules, formatting, line length"
    ),
    AgentConfig(
        name="Documentation Coverage",
        weight=float(os.getenv("DOCUMENTATION_WEIGHT", 12)),
        daily_token_budget=6_000_000,
        description="Analyzes docstring coverage, comment density, API docs"
    ),
    AgentConfig(
        name="Test Coverage Analyzer",
        weight=float(os.getenv("TEST_COVERAGE_WEIGHT", 14)),
        daily_token_budget=7_000_000,
        description="Analyzes test patterns, assertion quality, edge cases"
    ),
    AgentConfig(
        name="Coupling Analyzer",
        weight=float(os.getenv("COUPLING_WEIGHT", 18)),
        daily_token_budget=9_000_000,
        description="Measures afferent/efferent coupling, instability, abstractness"
    ),
    AgentConfig(
        name="Quality Gate",
        weight=float(os.getenv("QUALITY_GATE_WEIGHT", 15)),
        daily_token_budget=7_500_000,
        description="Pass/fail scoring, thresholds, trend analysis"
    ),
]


def get_agent_config(name: str) -> AgentConfig:
    """Get configuration for a specific agent by name."""
    for config in AGENT_CONFIGS:
        if config.name == name:
            return config
    raise ValueError(f"Unknown agent: {name}")


def get_total_daily_budget() -> int:
    """Calculate total daily token budget across all agents."""
    return sum(c.daily_token_budget for c in AGENT_CONFIGS)
