"""
PRISM Token Tracker
Tracks token consumption across all agents with budget management.
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class TokenUsage:
    """Token usage record for a single operation."""
    agent_name: str
    tokens_used: int
    operation: str
    timestamp: float
    success: bool = True
    file_path: str = ""


class TokenTracker:
    """Global token consumption tracker with budget enforcement."""

    def __init__(self, daily_budget: int = 68_000_000, monthly_budget: int = 1_600_000_000):
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        self._usage_history: List[TokenUsage] = []
        self._agent_totals: Dict[str, int] = defaultdict(int)
        self._daily_totals: Dict[str, int] = defaultdict(int)
        self._agent_success: Dict[str, Dict[str, int]] = defaultdict(lambda: {"success": 0, "fail": 0})
        self._start_time = time.time()

    def record_usage(self, agent_name: str, tokens: int, operation: str,
                     success: bool = True, file_path: str = "") -> TokenUsage:
        """Record token usage for an agent operation."""
        usage = TokenUsage(
            agent_name=agent_name,
            tokens_used=tokens,
            operation=operation,
            timestamp=time.time(),
            success=success,
            file_path=file_path
        )
        self._usage_history.append(usage)
        self._agent_totals[agent_name] += tokens

        today = datetime.now().strftime("%Y-%m-%d")
        self._daily_totals[today] += tokens

        if success:
            self._agent_success[agent_name]["success"] += 1
        else:
            self._agent_success[agent_name]["fail"] += 1

        return usage

    def get_agent_usage(self, agent_name: str) -> int:
        """Get total tokens used by a specific agent."""
        return self._agent_totals.get(agent_name, 0)

    def get_daily_usage(self, date: Optional[str] = None) -> int:
        """Get total tokens used on a specific date."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self._daily_totals.get(date, 0)

    def get_monthly_usage(self) -> int:
        """Get total tokens used this month."""
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total = 0
        for usage in self._usage_history:
            if usage.timestamp >= month_start.timestamp():
                total += usage.tokens_used
        return total

    def get_daily_budget_remaining(self) -> int:
        """Get remaining daily token budget."""
        used = self.get_daily_usage()
        return max(0, self.daily_budget - used)

    def can_proceed(self, estimated_tokens: int) -> bool:
        """Check if an operation can proceed within budget."""
        return self.get_daily_budget_remaining() >= estimated_tokens

    def get_agent_stats(self) -> Dict:
        """Get comprehensive statistics for all agents."""
        stats = {}
        for agent_name in self._agent_totals:
            success_data = self._agent_success[agent_name]
            total_ops = success_data["success"] + success_data["fail"]
            success_rate = (success_data["success"] / total_ops * 100) if total_ops > 0 else 0

            # Get recent usage (last 100 records)
            recent = [u for u in self._usage_history[-100:] if u.agent_name == agent_name]
            avg_tokens = sum(u.tokens_used for u in recent) / len(recent) if recent else 0

            stats[agent_name] = {
                "total_tokens": self._agent_totals[agent_name],
                "total_operations": total_ops,
                "success_count": success_data["success"],
                "fail_count": success_data["fail"],
                "success_rate": round(success_rate, 1),
                "avg_tokens_per_op": round(avg_tokens),
                "last_used": recent[-1].timestamp if recent else None
            }
        return stats

    def get_overall_stats(self) -> Dict:
        """Get overall platform statistics."""
        uptime = time.time() - self._start_time
        total_ops = len(self._usage_history)
        total_tokens = sum(u.tokens_used for u in self._usage_history)

        return {
            "uptime_seconds": round(uptime),
            "total_operations": total_ops,
            "total_tokens_consumed": total_tokens,
            "daily_budget": self.daily_budget,
            "monthly_budget": self.monthly_budget,
            "daily_used": self.get_daily_usage(),
            "daily_remaining": self.get_daily_budget_remaining(),
            "monthly_used": self.get_monthly_usage(),
            "daily_utilization": round(self.get_daily_usage() / self.daily_budget * 100, 1),
            "monthly_utilization": round(self.get_monthly_usage() / self.monthly_budget * 100, 1),
            "active_agents": len(self._agent_totals)
        }

    def get_hourly_breakdown(self) -> Dict[str, int]:
        """Get token usage broken down by hour for today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        hourly = defaultdict(int)
        for usage in self._usage_history:
            if usage.timestamp >= today_start:
                hour = datetime.fromtimestamp(usage.timestamp).strftime("%H:00")
                hourly[hour] += usage.tokens_used
        return dict(sorted(hourly.items()))

    def get_daily_history(self, days: int = 30) -> Dict[str, int]:
        """Get daily token usage for the last N days."""
        history = {}
        now = datetime.now()
        for i in range(days):
            date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            history[date] = self._daily_totals.get(date, 0)
        return dict(sorted(history.items()))


# Global singleton
_tracker: Optional[TokenTracker] = None


def get_tracker() -> TokenTracker:
    """Get or create the global token tracker."""
    global _tracker
    if _tracker is None:
        _tracker = TokenTracker()
    return _tracker
