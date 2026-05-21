"""
PRISM Analysis Agents
10 specialized agents for comprehensive code quality analysis.
"""

from agents.complexity_analyzer import ComplexityAnalyzerAgent
from agents.maintainability_scorer import MaintainabilityScorerAgent
from agents.code_smell_detector import CodeSmellDetectorAgent
from agents.naming_convention_checker import NamingConventionCheckerAgent
from agents.duplication_finder import DuplicationFinderAgent
from agents.style_compliance import StyleComplianceAgent
from agents.documentation_coverage import DocumentationCoverageAgent
from agents.test_coverage_analyzer import TestCoverageAnalyzerAgent
from agents.coupling_analyzer import CouplingAnalyzerAgent
from agents.quality_gate import QualityGateAgent

__all__ = [
    "ComplexityAnalyzerAgent",
    "MaintainabilityScorerAgent",
    "CodeSmellDetectorAgent",
    "NamingConventionCheckerAgent",
    "DuplicationFinderAgent",
    "StyleComplianceAgent",
    "DocumentationCoverageAgent",
    "TestCoverageAnalyzerAgent",
    "CouplingAnalyzerAgent",
    "QualityGateAgent",
]
