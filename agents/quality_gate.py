"""
PRISM - Quality Gate Agent
Estimated token consumption: ~15K tokens per analysis

Functions:
- Pass/fail quality scoring against configurable thresholds
- Weighted aggregation of all quality dimensions
- Trend analysis and risk assessment
- Quality gate configuration management
- Executive summary generation
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class QualityGateAgent:
    """Agent for quality gate pass/fail decisions and trend analysis."""

    AGENT_NAME = "Quality Gate"
    ESTIMATED_TOKENS = 15000

    # Default quality gate thresholds
    DEFAULT_THRESHOLDS = {
        "overall_score": {"min": 70, "target": 85},
        "complexity_score": {"min": 60, "target": 80},
        "maintainability_score": {"min": 65, "target": 85},
        "code_smell_score": {"min": 60, "target": 80},
        "duplication_score": {"min": 70, "target": 90},
        "style_score": {"min": 75, "target": 90},
        "documentation_score": {"min": 60, "target": 80},
        "test_coverage_score": {"min": 65, "target": 85},
        "coupling_score": {"min": 65, "target": 80},
    }

    # Weight for each dimension in overall score
    DIMENSION_WEIGHTS = {
        "complexity": 15,
        "maintainability": 12,
        "code_smell": 18,
        "naming": 10,
        "duplication": 20,
        "style": 10,
        "documentation": 12,
        "test_coverage": 14,
        "coupling": 18,
    }

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Perform quality gate analysis with pass/fail decision."""
        findings = []
        lines = code.split('\n')

        # 1. Calculate individual dimension scores
        dimension_scores = self._calculate_dimension_scores(code, lines, context)

        # 2. Check against thresholds
        threshold_findings = self._check_thresholds(dimension_scores)
        findings.extend(threshold_findings)

        # 3. Calculate weighted overall score
        overall_score = self._calculate_weighted_score(dimension_scores)

        # 4. Risk assessment
        risk_assessment = self._assess_risk(dimension_scores, overall_score)

        # 5. Generate recommendations
        recommendations = self._generate_recommendations(dimension_scores, overall_score)

        # 6. Trend analysis (based on current analysis)
        trend = self._analyze_trend(dimension_scores)

        # 7. Quality gate decision
        gate_passed = overall_score >= self.DEFAULT_THRESHOLDS["overall_score"]["min"]

        # Generate findings based on gate decision
        if not gate_passed:
            findings.append({
                "severity": "critical",
                "category": "quality_gate",
                "message": f"QUALITY GATE FAILED: Overall score {overall_score:.1f} below minimum threshold {self.DEFAULT_THRESHOLDS['overall_score']['min']}",
                "suggestion": "Address the critical and error findings to improve the quality score",
                "confidence": 1.0
            })

        # Add risk-based findings
        if risk_assessment["level"] == "high":
            findings.append({
                "severity": "error",
                "category": "risk_assessment",
                "message": f"High risk code: {risk_assessment['reason']}",
                "suggestion": "Prioritize fixing high-risk areas before deployment",
                "confidence": 0.85
            })

        # Calculate score
        score = overall_score

        metrics = {
            "score": score,
            "gate_passed": gate_passed,
            "gate_status": "PASS" if gate_passed else "FAIL",
            "thresholds": self.DEFAULT_THRESHOLDS,
            "dimension_scores": dimension_scores,
            "weighted_score": overall_score,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "trend": trend,
            "grade": self._calculate_grade(overall_score),
            "quality_dimensions_passed": sum(
                1 for dim, score in dimension_scores.items()
                if score >= self.DEFAULT_THRESHOLDS.get(f"{dim}_score", {}).get("min", 60)
            ),
            "total_quality_dimensions": len(dimension_scores),
            "timestamp": datetime.now().isoformat()
        }

        tokens_used = len(code) // 4 + len(findings) * 150 + 800
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _calculate_dimension_scores(self, code: str, lines: List[str], context: dict) -> Dict[str, float]:
        """Calculate scores for each quality dimension."""
        scores = {}

        # Complexity score
        scores["complexity"] = self._score_complexity(code, lines)

        # Maintainability score
        scores["maintainability"] = self._score_maintainability(code, lines)

        # Code smell score
        scores["code_smell"] = self._score_code_smells(code, lines)

        # Naming score
        scores["naming"] = self._score_naming(code)

        # Duplication score
        scores["duplication"] = self._score_duplication(lines)

        # Style score
        scores["style"] = self._score_style(code, lines)

        # Documentation score
        scores["documentation"] = self._score_documentation(code, lines)

        # Test coverage score
        scores["test_coverage"] = self._score_test_coverage(code)

        # Coupling score
        scores["coupling"] = self._score_coupling(code)

        return {k: round(v, 1) for k, v in scores.items()}

    def _score_complexity(self, code: str, lines: List[str]) -> float:
        """Score complexity dimension."""
        score = 100.0

        # Count decision points
        decision_points = len(re.findall(
            r'\b(if|elif|for|while|and|or|except|with)\b', code
        ))
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])

        if code_lines > 0:
            complexity_ratio = decision_points / code_lines
            if complexity_ratio > 0.3:
                score -= 30
            elif complexity_ratio > 0.2:
                score -= 20
            elif complexity_ratio > 0.1:
                score -= 10

        # Check for deeply nested code
        max_indent = max((len(line) - len(line.lstrip()) for line in lines if line.strip()), default=0)
        if max_indent > 20:
            score -= 20
        elif max_indent > 12:
            score -= 10

        return max(0, min(100, score))

    def _score_maintainability(self, code: str, lines: List[str]) -> float:
        """Score maintainability dimension."""
        score = 100.0

        # Module size
        total_lines = len(lines)
        if total_lines > 1000:
            score -= 25
        elif total_lines > 500:
            score -= 15
        elif total_lines > 300:
            score -= 5

        # Comment ratio
        comment_lines = len([l for l in lines if l.strip().startswith('#')])
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        if code_lines > 0:
            comment_ratio = comment_lines / code_lines
            if comment_ratio < 0.05:
                score -= 15
            elif comment_ratio < 0.1:
                score -= 5

        # TODO/FIXME count
        todos = len(re.findall(r'#\s*(TODO|FIXME|HACK|XXX)', code, re.IGNORECASE))
        score -= min(15, todos * 3)

        return max(0, min(100, score))

    def _score_code_smells(self, code: str, lines: List[str]) -> float:
        """Score code smell dimension."""
        score = 100.0

        # Long methods
        func_lengths = []
        current_length = 0
        for line in lines:
            if re.match(r'\s*(async\s+)?def\s+\w+', line):
                if current_length > 0:
                    func_lengths.append(current_length)
                current_length = 1
            elif current_length > 0:
                current_length += 1
        if current_length > 0:
            func_lengths.append(current_length)

        long_methods = sum(1 for l in func_lengths if l > 50)
        score -= long_methods * 10

        # Large classes
        class_count = len(re.findall(r'class\s+\w+', code))
        if class_count > 5:
            score -= 15
        elif class_count > 3:
            score -= 5

        # Magic numbers
        magic_numbers = len(re.findall(r'(?<=[\s=(,])\d{3,}(?=[\s,)\]])', code))
        score -= min(10, magic_numbers)

        return max(0, min(100, score))

    def _score_naming(self, code: str) -> float:
        """Score naming convention dimension."""
        score = 100.0

        # Check for single letter variables
        single_letter = len(re.findall(r'\b[a-z]\b(?!\s*=[\s=])', code))
        score -= min(15, single_letter)

        # Check for inconsistent naming
        snake_case = len(re.findall(r'\b[a-z]+_[a-z]+\b', code))
        camel_case = len(re.findall(r'\b[a-z]+[A-Z][a-z]+\b', code))

        if snake_case > 0 and camel_case > 0:
            ratio = min(snake_case, camel_case) / max(snake_case, camel_case)
            if ratio > 0.3:
                score -= 10  # Mixed naming styles

        return max(0, min(100, score))

    def _score_duplication(self, lines: List[str]) -> float:
        """Score duplication dimension."""
        score = 100.0

        # Count duplicate lines
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 20:
                line_counts[stripped] = line_counts.get(stripped, 0) + 1

        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        total_lines = len([l for l in lines if l.strip()])

        if total_lines > 0:
            dup_ratio = duplicate_lines / total_lines * 100
            if dup_ratio > 20:
                score -= 40
            elif dup_ratio > 10:
                score -= 25
            elif dup_ratio > 5:
                score -= 15
            elif dup_ratio > 2:
                score -= 5

        return max(0, min(100, score))

    def _score_style(self, code: str, lines: List[str]) -> float:
        """Score style compliance dimension."""
        score = 100.0

        # Line length violations
        long_lines = sum(1 for line in lines if len(line.rstrip()) > 120)
        very_long_lines = sum(1 for line in lines if len(line.rstrip()) > 200)
        score -= very_long_lines * 5
        score -= long_lines * 1

        # Trailing whitespace
        trailing_ws = sum(1 for line in lines if line != line.rstrip())
        score -= min(10, trailing_ws)

        # Tabs vs spaces
        if any('\t' in line for line in lines):
            score -= 10

        # Semicolons in Python
        semicolons = sum(1 for line in lines if line.strip().endswith(';'))
        score -= min(10, semicolons * 2)

        return max(0, min(100, score))

    def _score_documentation(self, code: str, lines: List[str]) -> float:
        """Score documentation dimension."""
        score = 100.0

        # Module docstring
        if not code.strip().startswith(('"""', "'''", '#')):
            score -= 15

        # Function docstrings
        functions = list(re.finditer(r'(?:async\s+)?def\s+(\w+)', code))
        undocumented = 0
        for func_match in functions:
            after_func = code[func_match.end():].lstrip()
            if not (after_func.startswith('"""') or after_func.startswith("'''")):
                undocumented += 1

        if functions:
            doc_ratio = (len(functions) - undocumented) / len(functions)
            score -= (1 - doc_ratio) * 30

        # Comment density
        comment_lines = len([l for l in lines if l.strip().startswith('#')])
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        if code_lines > 0:
            comment_density = comment_lines / code_lines
            if comment_density < 0.05:
                score -= 15

        return max(0, min(100, score))

    def _score_test_coverage(self, code: str) -> float:
        """Score test coverage dimension."""
        score = 100.0

        test_functions = len(re.findall(r'def\s+test_\w+', code))
        total_functions = len(re.findall(r'def\s+\w+', code))

        if total_functions > 0:
            test_ratio = test_functions / total_functions
            if test_ratio < 0.1:
                score -= 40
            elif test_ratio < 0.3:
                score -= 25
            elif test_ratio < 0.5:
                score -= 10

        # Check for assertions
        assertions = len(re.findall(r'\bassert\w*\b', code))
        if test_functions > 0 and assertions < test_functions:
            score -= 15

        return max(0, min(100, score))

    def _score_coupling(self, code: str) -> float:
        """Score coupling dimension."""
        score = 100.0

        # Import count
        imports = len(re.findall(r'^(?:from\s+\S+\s+)?import\s+', code, re.MULTILINE))
        if imports > 20:
            score -= 25
        elif imports > 15:
            score -= 15
        elif imports > 10:
            score -= 5

        # Star imports
        star_imports = len(re.findall(r'from\s+\S+\s+import\s+\*', code))
        score -= star_imports * 15

        # Global variables
        globals_count = len(re.findall(r'^[A-Z_][A-Z_0-9]*\s*=', code, re.MULTILINE))
        score -= min(15, globals_count * 3)

        return max(0, min(100, score))

    def _check_thresholds(self, dimension_scores: Dict[str, float]) -> List[Dict]:
        """Check dimension scores against thresholds."""
        findings = []

        for dim, score in dimension_scores.items():
            threshold_key = f"{dim}_score"
            threshold = self.DEFAULT_THRESHOLDS.get(threshold_key)

            if threshold:
                if score < threshold["min"]:
                    findings.append({
                        "severity": "error",
                        "category": "threshold_violation",
                        "message": f"{dim.replace('_', ' ').title()} score {score:.1f} below minimum threshold {threshold['min']}",
                        "suggestion": f"Improve {dim.replace('_', ' ')} to meet minimum quality standards",
                        "confidence": 0.95
                    })
                elif score < threshold["target"]:
                    findings.append({
                        "severity": "warning",
                        "category": "below_target",
                        "message": f"{dim.replace('_', ' ').title()} score {score:.1f} below target {threshold['target']}",
                        "suggestion": f"Consider improving {dim.replace('_', ' ')} to reach target quality",
                        "confidence": 0.85
                    })

        return findings

    def _calculate_weighted_score(self, dimension_scores: Dict[str, float]) -> float:
        """Calculate weighted overall score."""
        weighted_sum = 0
        total_weight = 0

        for dim, score in dimension_scores.items():
            weight = self.DIMENSION_WEIGHTS.get(dim, 10)
            weighted_sum += score * weight
            total_weight += weight

        return round(weighted_sum / max(1, total_weight), 1)

    def _assess_risk(self, dimension_scores: Dict[str, float], overall_score: float) -> Dict:
        """Assess risk level based on quality metrics."""
        risk_factors = []
        risk_score = 0

        # Check for critical dimensions
        critical_dims = ["complexity", "coupling", "code_smell"]
        for dim in critical_dims:
            if dim in dimension_scores and dimension_scores[dim] < 50:
                risk_factors.append(f"Low {dim} score ({dimension_scores[dim]:.1f})")
                risk_score += 25

        # Check overall score
        if overall_score < 50:
            risk_factors.append(f"Very low overall score ({overall_score:.1f})")
            risk_score += 30
        elif overall_score < 70:
            risk_factors.append(f"Below threshold overall score ({overall_score:.1f})")
            risk_score += 15

        # Determine risk level
        if risk_score >= 50:
            level = "high"
        elif risk_score >= 25:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "score": risk_score,
            "factors": risk_factors,
            "reason": "; ".join(risk_factors) if risk_factors else "No significant risk factors"
        }

    def _generate_recommendations(self, dimension_scores: Dict[str, float],
                                 overall_score: float) -> List[Dict]:
        """Generate prioritized recommendations for improvement."""
        recommendations = []

        # Sort dimensions by score (lowest first)
        sorted_dims = sorted(dimension_scores.items(), key=lambda x: x[1])

        for dim, score in sorted_dims[:3]:
            if score < 70:
                recommendations.append({
                    "priority": "high" if score < 50 else "medium",
                    "dimension": dim,
                    "current_score": score,
                    "target_score": self.DEFAULT_THRESHOLDS.get(f"{dim}_score", {}).get("target", 80),
                    "actions": self._get_dimension_actions(dim, score)
                })

        # Add general recommendations if overall score is low
        if overall_score < 70:
            recommendations.append({
                "priority": "high",
                "dimension": "overall",
                "current_score": overall_score,
                "target_score": 85,
                "actions": [
                    "Conduct a comprehensive code review session",
                    "Establish and enforce coding standards",
                    "Implement automated quality checks in CI/CD pipeline",
                    "Schedule regular refactoring sprints"
                ]
            })

        return recommendations

    def _get_dimension_actions(self, dimension: str, score: float) -> List[str]:
        """Get specific improvement actions for a dimension."""
        actions_map = {
            "complexity": [
                "Break complex functions into smaller, focused units",
                "Reduce nesting depth using early returns",
                "Extract complex conditions into named functions",
                "Use strategy pattern to reduce conditional branches"
            ],
            "maintainability": [
                "Add comprehensive documentation and comments",
                "Reduce technical debt by addressing TODO/FIXME items",
                "Improve code organization and module structure",
                "Refactor large files into smaller modules"
            ],
            "code_smell": [
                "Refactor god classes into smaller, focused classes",
                "Extract long methods into helper functions",
                "Remove dead code and unused variables",
                "Apply Single Responsibility Principle"
            ],
            "naming": [
                "Use consistent naming conventions throughout",
                "Replace abbreviations with descriptive names",
                "Ensure names clearly convey purpose and intent",
                "Follow language-specific naming standards"
            ],
            "duplication": [
                "Extract duplicate code into shared functions",
                "Use inheritance or composition to share behavior",
                "Apply DRY (Don't Repeat Yourself) principle",
                "Create utility functions for common operations"
            ],
            "style": [
                "Configure and run automated code formatter",
                "Fix line length and whitespace issues",
                "Organize imports according to standards",
                "Use consistent string quoting style"
            ],
            "documentation": [
                "Add docstrings to all public functions and classes",
                "Document complex algorithms and business logic",
                "Include parameter and return type documentation",
                "Add usage examples in docstrings"
            ],
            "test_coverage": [
                "Write unit tests for critical business logic",
                "Add edge case tests for boundary conditions",
                "Implement integration tests for key workflows",
                "Add regression tests for reported bugs"
            ],
            "coupling": [
                "Apply dependency injection for loose coupling",
                "Use interfaces/protocols to define contracts",
                "Reduce circular dependencies",
                "Apply Interface Segregation Principle"
            ]
        }

        return actions_map.get(dimension, ["Review and improve this quality dimension"])

    def _analyze_trend(self, dimension_scores: Dict[str, float]) -> Dict:
        """Analyze quality trends (simplified - based on current snapshot)."""
        avg_score = sum(dimension_scores.values()) / max(1, len(dimension_scores))

        # Determine trend direction based on score distribution
        high_scores = sum(1 for s in dimension_scores.values() if s > 80)
        low_scores = sum(1 for s in dimension_scores.values() if s < 60)

        if high_scores > len(dimension_scores) * 0.7:
            direction = "improving"
            stability = "stable"
        elif low_scores > len(dimension_scores) * 0.5:
            direction = "declining"
            stability = "concerning"
        else:
            direction = "mixed"
            stability = "variable"

        return {
            "direction": direction,
            "stability": stability,
            "average_score": round(avg_score, 1),
            "dimensions_above_target": sum(
                1 for dim, score in dimension_scores.items()
                if score >= self.DEFAULT_THRESHOLDS.get(f"{dim}_score", {}).get("target", 80)
            ),
            "dimensions_below_minimum": sum(
                1 for dim, score in dimension_scores.items()
                if score < self.DEFAULT_THRESHOLDS.get(f"{dim}_score", {}).get("min", 60)
            )
        }

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 55:
            return "C-"
        elif score >= 50:
            return "D"
        else:
            return "F"
