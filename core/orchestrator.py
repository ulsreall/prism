"""
PRISM Orchestrator
Coordinates all analysis agents and manages the analysis pipeline.
"""

import asyncio
import time
import importlib
from typing import Dict, List, Optional, Any
from core.config import AGENT_CONFIGS, PlatformConfig
from core.models import AnalysisReport, AgentResult, Finding
from core.token_tracker import get_tracker


class AgentOrchestrator:
    """Orchestrates code quality analysis across all agents."""

    def __init__(self, config: Optional[PlatformConfig] = None):
        self.config = config or PlatformConfig()
        self.agents: Dict[str, Any] = {}
        self._load_agents()

    def _load_agents(self):
        """Dynamically load all analysis agents."""
        agent_modules = {
            "Complexity Analyzer": "agents.complexity_analyzer",
            "Maintainability Scorer": "agents.maintainability_scorer",
            "Code Smell Detector": "agents.code_smell_detector",
            "Naming Convention Checker": "agents.naming_convention_checker",
            "Duplication Finder": "agents.duplication_finder",
            "Style Compliance": "agents.style_compliance",
            "Documentation Coverage": "agents.documentation_coverage",
            "Test Coverage Analyzer": "agents.test_coverage_analyzer",
            "Coupling Analyzer": "agents.coupling_analyzer",
            "Quality Gate": "agents.quality_gate",
        }

        for name, module_path in agent_modules.items():
            try:
                module = importlib.import_module(module_path)
                # Find the agent class (convention: first class ending in 'Agent')
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        attr_name.endswith('Agent') and
                        hasattr(attr, 'analyze')):
                        self.agents[name] = attr()
                        break
            except Exception as e:
                print(f"Warning: Failed to load agent '{name}': {e}")

    async def analyze_code(self, code: str, file_path: str = "",
                          language: str = "python",
                          agents: Optional[List[str]] = None) -> AnalysisReport:
        """Run full code analysis across all (or selected) agents."""
        report = AnalysisReport(
            file_path=file_path,
            language=language
        )

        context = {
            "file_path": file_path,
            "language": language,
            "line_count": len(code.split('\n')),
            "char_count": len(code),
        }

        target_agents = agents or list(self.agents.keys())
        tracker = get_tracker()

        # Run agents concurrently
        tasks = []
        for agent_name in target_agents:
            if agent_name in self.agents:
                tasks.append(self._run_agent(
                    agent_name, self.agents[agent_name], code, context, tracker
                ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, AgentResult):
                report.agent_results.append(result)
            elif isinstance(result, Exception):
                report.agent_results.append(AgentResult(
                    agent_name="unknown",
                    success=False,
                    error_message=str(result)
                ))

        report.calculate_overall_score()
        return report

    async def _run_agent(self, name: str, agent: Any, code: str,
                        context: dict, tracker) -> AgentResult:
        """Run a single agent with error handling and token tracking."""
        start_time = time.time()
        try:
            result = await agent.analyze(code, context)
            duration = (time.time() - start_time) * 1000

            tokens = result.get("tokens_used", 0)
            tracker.record_usage(name, tokens, "analyze", success=True)

            findings = []
            for f in result.get("findings", []):
                if isinstance(f, dict):
                    findings.append(Finding(
                        agent=name,
                        severity=f.get("severity", "info"),
                        category=f.get("category", ""),
                        message=f.get("message", ""),
                        file_path=f.get("file_path", ""),
                        line_start=f.get("line_start", 0),
                        line_end=f.get("line_end", 0),
                        code_snippet=f.get("code_snippet", ""),
                        suggestion=f.get("suggestion", ""),
                        confidence=f.get("confidence", 0.8)
                    ))
                elif isinstance(f, Finding):
                    f.agent = name
                    findings.append(f)

            return AgentResult(
                agent_name=name,
                findings=findings,
                metrics=result.get("metrics", {}),
                tokens_used=tokens,
                duration_ms=duration,
                success=True
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            tracker.record_usage(name, 0, "analyze", success=False)
            return AgentResult(
                agent_name=name,
                success=False,
                error_message=str(e),
                duration_ms=duration
            )

    def get_agent_info(self) -> List[Dict]:
        """Get information about all loaded agents."""
        info = []
        tracker = get_tracker()
        stats = tracker.get_agent_stats()

        for config in AGENT_CONFIGS:
            agent_data = {
                "name": config.name,
                "description": config.description,
                "weight": config.weight,
                "daily_token_budget": config.daily_token_budget,
                "enabled": config.enabled,
                "loaded": config.name in self.agents,
            }
            if config.name in stats:
                agent_data.update(stats[config.name])
            info.append(agent_data)
        return info


# Singleton
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create the global orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
