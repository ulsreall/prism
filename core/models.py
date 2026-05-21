"""
PRISM Data Models
Pydantic-style data models for analysis results and findings.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class Severity(Enum):
    """Finding severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class QualityLevel(Enum):
    """Quality assessment levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class Finding:
    """A single code quality finding."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent: str = ""
    severity: str = "info"
    category: str = ""
    message: str = ""
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    code_snippet: str = ""
    suggestion: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "confidence": self.confidence
        }


@dataclass
class AgentResult:
    """Result from a single agent analysis."""
    agent_name: str
    findings: List[Finding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    duration_ms: float = 0
    success: bool = True
    error_message: str = ""

    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "findings": [f.to_dict() for f in self.findings],
            "metrics": self.metrics,
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class AnalysisReport:
    """Complete analysis report combining all agent results."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    language: str = "python"
    timestamp: float = field(default_factory=time.time)
    agent_results: List[AgentResult] = field(default_factory=list)
    overall_score: float = 0.0
    quality_level: str = "fair"
    total_tokens: int = 0
    total_duration_ms: float = 0
    summary: Dict[str, Any] = field(default_factory=dict)

    def calculate_overall_score(self):
        """Calculate weighted overall quality score."""
        if not self.agent_results:
            return 0.0

        weights = {
            "Complexity Analyzer": 15,
            "Maintainability Scorer": 12,
            "Code Smell Detector": 18,
            "Naming Convention Checker": 10,
            "Duplication Finder": 20,
            "Style Compliance": 10,
            "Documentation Coverage": 12,
            "Test Coverage Analyzer": 14,
            "Coupling Analyzer": 18,
            "Quality Gate": 15,
        }

        weighted_sum = 0
        total_weight = 0
        for result in self.agent_results:
            if result.success and "score" in result.metrics:
                weight = weights.get(result.agent_name, 10)
                weighted_sum += result.metrics["score"] * weight
                total_weight += weight

        if total_weight > 0:
            self.overall_score = round(weighted_sum / total_weight, 1)

        # Determine quality level
        if self.overall_score >= 90:
            self.quality_level = "excellent"
        elif self.overall_score >= 75:
            self.quality_level = "good"
        elif self.overall_score >= 60:
            self.quality_level = "fair"
        elif self.overall_score >= 40:
            self.quality_level = "poor"
        else:
            self.quality_level = "critical"

        # Build summary
        self.total_tokens = sum(r.tokens_used for r in self.agent_results)
        self.total_duration_ms = sum(r.duration_ms for r in self.agent_results)
        self.summary = {
            "total_findings": sum(len(r.findings) for r in self.agent_results),
            "critical_findings": sum(
                len([f for f in r.findings if f.severity == "critical"])
                for r in self.agent_results
            ),
            "error_findings": sum(
                len([f for f in r.findings if f.severity == "error"])
                for r in self.agent_results
            ),
            "warning_findings": sum(
                len([f for f in r.findings if f.severity == "warning"])
                for r in self.agent_results
            ),
            "agents_run": len(self.agent_results),
            "agents_succeeded": sum(1 for r in self.agent_results if r.success),
        }

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "language": self.language,
            "timestamp": self.timestamp,
            "overall_score": self.overall_score,
            "quality_level": self.quality_level,
            "total_tokens": self.total_tokens,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "summary": self.summary,
            "agent_results": [r.to_dict() for r in self.agent_results]
        }
