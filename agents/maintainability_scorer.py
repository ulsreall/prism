"""
PRISM - Maintainability Scorer Agent
Estimated token consumption: ~14K tokens per analysis

Analyzes:
- Maintainability Index (MI) calculation
- Technical debt ratio estimation
- Code churn risk indicators
- Modularity assessment
- Dependency health scoring
"""

import re
import math
from typing import Dict, List, Any


class MaintainabilityScorerAgent:
    """Agent for scoring code maintainability."""

    AGENT_NAME = "Maintainability Scorer"
    ESTIMATED_TOKENS = 14000

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Analyze code maintainability across multiple dimensions."""
        findings = []
        lines = code.split('\n')

        # 1. Maintainability Index (simplified Microsoft formula)
        mi = self._calculate_maintainability_index(code)

        # 2. Technical Debt Ratio
        debt_ratio = self._calculate_technical_debt(code, lines)

        # 3. Module size analysis
        module_metrics = self._analyze_module_size(lines)

        # 4. Coupling indicators
        coupling_score = self._analyze_coupling_indicators(code)

        # 5. Code organization
        org_score = self._analyze_code_organization(code, lines)

        # Generate findings
        if mi < 20:
            findings.append({
                "severity": "critical",
                "category": "maintainability",
                "message": f"Very low Maintainability Index: {mi:.1f}/100",
                "suggestion": "This code is extremely difficult to maintain. Consider a complete refactoring.",
                "confidence": 0.95
            })
        elif mi < 40:
            findings.append({
                "severity": "warning",
                "category": "maintainability",
                "message": f"Low Maintainability Index: {mi:.1f}/100",
                "suggestion": "Reduce complexity, improve naming, and add documentation.",
                "confidence": 0.9
            })

        if debt_ratio > 5:
            findings.append({
                "severity": "error",
                "category": "technical_debt",
                "message": f"High technical debt ratio: {debt_ratio:.1f}%",
                "suggestion": "Allocate time for refactoring to reduce accumulated technical debt.",
                "confidence": 0.85
            })
        elif debt_ratio > 3:
            findings.append({
                "severity": "warning",
                "category": "technical_debt",
                "message": f"Moderate technical debt ratio: {debt_ratio:.1f}%",
                "suggestion": "Schedule regular refactoring sessions to prevent debt accumulation.",
                "confidence": 0.8
            })

        if module_metrics["longest_function"] > 50:
            findings.append({
                "severity": "warning",
                "category": "module_size",
                "message": f"Longest function is {module_metrics['longest_function']} lines",
                "suggestion": "Break long functions into smaller, focused units (aim for <30 lines).",
                "confidence": 0.9
            })

        if module_metrics["total_lines"] > 500:
            findings.append({
                "severity": "warning",
                "category": "module_size",
                "message": f"Large module: {module_metrics['total_lines']} lines",
                "suggestion": "Consider splitting into smaller modules for better maintainability.",
                "confidence": 0.85
            })

        # Calculate overall score
        score = self._calculate_score(mi, debt_ratio, module_metrics, coupling_score, org_score)

        metrics = {
            "score": score,
            "maintainability_index": round(mi, 1),
            "technical_debt_ratio": round(debt_ratio, 1),
            "module_metrics": module_metrics,
            "coupling_indicators": coupling_score,
            "organization_score": org_score,
            "estimated_maintenance_hours": self._estimate_maintenance_time(mi, debt_ratio, module_metrics)
        }

        tokens_used = len(code) // 4 + len(findings) * 120 + 400
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _calculate_maintainability_index(self, code: str) -> float:
        """
        Simplified Microsoft Maintainability Index.
        MI = max(0, (171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)) * 100 / 171)
        """
        lines = code.split('\n')
        loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])

        # Halstead Volume (simplified)
        unique_operators = len(set(re.findall(r'[+\-*/=<>!&|^~%]+|' +
            r'\b(and|or|not|in|is|if|else|for|while|return|class|def|import)\b', code)))
        unique_operands = len(set(re.findall(r'\b[a-zA-Z_]\w*\b', code))) - unique_operators
        total_ops = len(re.findall(r'[+\-*/=<>!&|^~%]+|' +
            r'\b(and|or|not|in|is|if|else|for|while|return|class|def|import)\b', code))
        total_operands = len(re.findall(r'\b[a-zA-Z_]\w*\b', code)) - total_ops

        vocabulary = max(1, unique_operators + unique_operands)
        length = max(1, total_ops + total_operands)
        hv = length * math.log2(vocabulary) if vocabulary > 1 else 1

        # Cyclomatic complexity (simplified)
        cc_patterns = [r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
                       r'\band\b', r'\bor\b', r'\bexcept\b', r'\bwith\b']
        cc = 1
        for pattern in cc_patterns:
            cc += len(re.findall(pattern, code))

        # MI formula
        hv_log = math.log(max(1, hv))
        loc_log = math.log(max(1, loc))
        mi = max(0, (171 - 5.2 * hv_log - 0.23 * cc - 16.2 * loc_log) * 100 / 171)

        return mi

    def _calculate_technical_debt(self, code: str, lines: List[str]) -> float:
        """Estimate technical debt ratio as percentage."""
        debt_indicators = 0
        total_checks = 0

        # TODO/FIXME/HACK comments
        debt_comments = len(re.findall(r'#\s*(TODO|FIXME|HACK|XXX|TEMP|WORKAROUND)', code, re.IGNORECASE))
        debt_indicators += min(debt_comments * 2, 10)
        total_checks += 10

        # Magic numbers
        magic_numbers = len(re.findall(r'(?<=[\s=(,])\d{2,}(?=[\s,)\]])', code))
        debt_indicators += min(magic_numbers, 10)
        total_checks += 10

        # Duplicate code patterns (simplified)
        line_set = set()
        duplicates = 0
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 20:
                if stripped in line_set:
                    duplicates += 1
                line_set.add(stripped)
        debt_indicators += min(duplicates * 2, 15)
        total_checks += 15

        # Long parameter lists
        long_params = len(re.findall(r'def\s+\w+\s*\([^)]{80,}\)', code))
        debt_indicators += long_params * 3
        total_checks += 5

        # Deeply nested code
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        if max_indent > 16:
            debt_indicators += 10
        total_checks += 10

        return (debt_indicators / total_checks * 100) if total_checks > 0 else 0

    def _analyze_module_size(self, lines: List[str]) -> Dict:
        """Analyze module size metrics."""
        total_lines = len(lines)
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        comment_lines = len([l for l in lines if l.strip().startswith('#')])
        blank_lines = total_lines - code_lines - comment_lines

        # Function lengths
        func_lengths = []
        current_func_len = 0
        in_func = False
        for line in lines:
            if re.match(r'\s*(async\s+)?def\s+\w+', line):
                if in_func and current_func_len > 0:
                    func_lengths.append(current_func_len)
                in_func = True
                current_func_len = 1
            elif in_func:
                current_func_len += 1
        if in_func and current_func_len > 0:
            func_lengths.append(current_func_len)

        # Class sizes
        class_sizes = []
        current_class_size = 0
        in_class = False
        for line in lines:
            if re.match(r'\s*class\s+\w+', line):
                if in_class and current_class_size > 0:
                    class_sizes.append(current_class_size)
                in_class = True
                current_class_size = 1
            elif in_class:
                current_class_size += 1
        if in_class and current_class_size > 0:
            class_sizes.append(current_class_size)

        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "comment_ratio": round(comment_lines / max(1, code_lines) * 100, 1),
            "function_count": len(func_lengths),
            "class_count": len(class_sizes),
            "avg_function_length": round(sum(func_lengths) / max(1, len(func_lengths)), 1),
            "longest_function": max(func_lengths) if func_lengths else 0,
            "avg_class_size": round(sum(class_sizes) / max(1, len(class_sizes)), 1) if class_sizes else 0,
            "longest_class": max(class_sizes) if class_sizes else 0
        }

    def _analyze_coupling_indicators(self, code: str) -> float:
        """Analyze coupling indicators (0-100, higher is better = less coupling)."""
        score = 100.0

        # Import count
        imports = len(re.findall(r'^(?:from\s+\S+\s+)?import\s+', code, re.MULTILINE))
        if imports > 15:
            score -= 20
        elif imports > 10:
            score -= 10

        # Global variables
        globals_count = len(re.findall(r'^[A-Z_][A-Z_0-9]*\s*=', code, re.MULTILINE))
        score -= min(globals_count * 5, 20)

        # Star imports
        star_imports = len(re.findall(r'from\s+\S+\s+import\s+\*', code))
        score -= star_imports * 15

        return max(0, score)

    def _analyze_code_organization(self, code: str, lines: List[str]) -> float:
        """Analyze code organization quality (0-100)."""
        score = 100.0

        # Check for proper module structure
        has_docstring = bool(re.search(r'^("""|\').*("""|\')', code.strip(), re.DOTALL))
        if not has_docstring:
            score -= 15

        # Check imports are at top
        import_section_ended = False
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('"""'):
                if re.match(r'^(from|import)\s', stripped):
                    if import_section_ended:
                        score -= 10  # Import not at top
                        break
                elif stripped:
                    import_section_ended = True

        # Check for consistent class organization
        classes = re.findall(r'class\s+(\w+)', code)
        if len(classes) > 3:
            score -= 10  # Too many classes in one file

        return max(0, score)

    def _calculate_score(self, mi: float, debt_ratio: float, module_metrics: Dict,
                        coupling_score: float, org_score: float) -> float:
        """Calculate overall maintainability score (0-100)."""
        # Weighted combination
        mi_normalized = min(100, mi)  # MI is already 0-100
        debt_normalized = max(0, 100 - debt_ratio * 10)  # Lower debt = higher score

        score = (
            mi_normalized * 0.35 +
            debt_normalized * 0.25 +
            coupling_score * 0.20 +
            org_score * 0.20
        )
        return max(0, min(100, round(score, 1)))

    def _estimate_maintenance_time(self, mi: float, debt_ratio: float,
                                   module_metrics: Dict) -> float:
        """Estimate maintenance effort in hours."""
        base_hours = module_metrics["total_lines"] / 100
        mi_factor = max(1, (100 - mi) / 20)
        debt_factor = 1 + debt_ratio / 10
        return round(base_hours * mi_factor * debt_factor, 1)
