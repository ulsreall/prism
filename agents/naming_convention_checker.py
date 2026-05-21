"""
PRISM - Naming Convention Checker Agent
Estimated token consumption: ~12K tokens per analysis

Analyzes:
- PEP8 naming conventions (snake_case, CamelCase, UPPER_CASE)
- Consistency across codebase
- Name length and readability
- Abbreviation detection
- Semantic naming quality
"""

import re
from typing import Dict, List, Any, Set
from collections import defaultdict


class NamingConventionCheckerAgent:
    """Agent for checking naming conventions and consistency."""

    AGENT_NAME = "Naming Convention Checker"
    ESTIMATED_TOKENS = 12000

    # Naming patterns
    SNAKE_CASE = re.compile(r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$')
    CAMEL_CASE = re.compile(r'^[a-z][a-zA-Z0-9]*$')
    PASCAL_CASE = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
    UPPER_SNAKE = re.compile(r'^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$')

    # Common abbreviations that reduce readability
    BAD_ABBREVIATIONS = {
        'tmp', 'temp', 'val', 'num', 'cnt', 'idx', 'pos', 'len', 'buf',
        'ptr', 'ctx', 'cb', 'fn', 'str', 'lst', 'dict', 'obj', 'arr',
        'msg', 'err', 'res', 'req', 'ret', 'arg', 'args', 'kwargs',
        'btn', 'txt', 'img', 'src', 'dst', 'ref', 'attr', 'elem'
    }

    # Common good naming patterns
    GOOD_PATTERNS = {
        'is_': 'boolean',
        'has_': 'boolean',
        'can_': 'boolean',
        'should_': 'boolean',
        'get_': 'getter',
        'set_': 'setter',
        'create_': 'factory',
        'update_': 'modifier',
        'delete_': 'remover',
        'validate_': 'validator',
        'calculate_': 'calculator',
        'convert_': 'converter',
        'parse_': 'parser',
        'format_': 'formatter',
    }

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Analyze naming conventions across the codebase."""
        findings = []
        lines = code.split('\n')

        # 1. Check function/method names
        func_findings = self._check_function_names(code)
        findings.extend(func_findings)

        # 2. Check class names
        class_findings = self._check_class_names(code)
        findings.extend(class_findings)

        # 3. Check variable names
        var_findings = self._check_variable_names(code)
        findings.extend(var_findings)

        # 4. Check constant names
        const_findings = self._check_constant_names(code)
        findings.extend(const_findings)

        # 5. Check parameter names
        param_findings = self._check_parameter_names(code)
        findings.extend(param_findings)

        # 6. Check name lengths
        length_findings = self._check_name_lengths(code)
        findings.extend(length_findings)

        # 7. Check for abbreviations
        abbr_findings = self._check_abbreviations(code)
        findings.extend(abbr_findings)

        # 8. Consistency analysis
        consistency = self._analyze_consistency(code)

        # Calculate metrics
        all_names = self._extract_all_names(code)
        naming_stats = self._calculate_naming_stats(all_names)

        score = self._calculate_score(findings, all_names, consistency)

        metrics = {
            "score": score,
            "total_names_checked": len(all_names),
            "naming_style_distribution": naming_stats,
            "consistency_score": consistency["score"],
            "consistency_details": consistency,
            "avg_name_length": round(
                sum(len(n["name"]) for n in all_names) / max(1, len(all_names)), 1
            ),
            "issues_per_100_names": round(
                len(findings) / max(1, len(all_names)) * 100, 2
            )
        }

        tokens_used = len(code) // 4 + len(findings) * 100 + 400
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _check_function_names(self, code: str) -> List[Dict]:
        """Check function/method naming conventions."""
        findings = []
        for match in re.finditer(r'(?:async\s+)?def\s+(\w+)', code):
            name = match.group(1)
            line_num = code[:match.start()].count('\n') + 1

            # Special methods (dunder) are exempt
            if name.startswith('__') and name.endswith('__'):
                continue

            # Private methods
            if name.startswith('_'):
                actual_name = name[1:]
            else:
                actual_name = name

            # Functions should be snake_case
            if not self.SNAKE_CASE.match(actual_name):
                # Check if it's camelCase (common mistake)
                if self.CAMEL_CASE.match(actual_name):
                    findings.append({
                        "severity": "warning",
                        "category": "naming_convention",
                        "message": f"Function '{name}' uses camelCase, should be snake_case",
                        "line_start": line_num,
                        "suggestion": f"Rename to '{self._to_snake_case(actual_name)}'",
                        "confidence": 0.95
                    })
                elif '_' not in actual_name and len(actual_name) > 10:
                    findings.append({
                        "severity": "info",
                        "category": "naming_convention",
                        "message": f"Function '{name}' should use snake_case with word separators",
                        "line_start": line_num,
                        "confidence": 0.8
                    })

        return findings

    def _check_class_names(self, code: str) -> List[Dict]:
        """Check class naming conventions."""
        findings = []
        for match in re.finditer(r'class\s+(\w+)', code):
            name = match.group(1)
            line_num = code[:match.start()].count('\n') + 1

            # Classes should be PascalCase
            if not self.PASCAL_CASE.match(name):
                if self.SNAKE_CASE.match(name):
                    findings.append({
                        "severity": "warning",
                        "category": "naming_convention",
                        "message": f"Class '{name}' uses snake_case, should be PascalCase",
                        "line_start": line_num,
                        "suggestion": f"Rename to '{self._to_pascal_case(name)}'",
                        "confidence": 0.95
                    })
                elif name.startswith('_'):
                    findings.append({
                        "severity": "info",
                        "category": "naming_convention",
                        "message": f"Private class '{name}' - consider if private classes are necessary",
                        "line_start": line_num,
                        "confidence": 0.6
                    })

            # Check for generic names
            generic_names = {'Data', 'Info', 'Manager', 'Handler', 'Helper', 'Utils',
                           'Stuff', 'Thing', 'Object', 'Base'}
            if name in generic_names:
                findings.append({
                    "severity": "info",
                    "category": "naming_quality",
                    "message": f"Class '{name}' has a generic name that doesn't convey purpose",
                    "line_start": line_num,
                    "suggestion": "Use a more descriptive name that reflects the class's responsibility",
                    "confidence": 0.7
                })

        return findings

    def _check_variable_names(self, code: str) -> List[Dict]:
        """Check variable naming conventions."""
        findings = []
        # Find assignments (simplified)
        for match in re.finditer(r'^(\s*)([a-zA-Z_]\w*)\s*=(?!=)', code, re.MULTILINE):
            indent = match.group(1)
            name = match.group(2)
            line_num = code[:match.start()].count('\n') + 1

            # Skip if it's a known keyword or inside a function
            if name in ('self', 'cls', 'def', 'class', 'import', 'from', 'return',
                       'if', 'else', 'for', 'while', 'try', 'except', 'finally',
                       'with', 'as', 'raise', 'yield', 'lambda', 'pass', 'break',
                       'continue', 'global', 'nonlocal', 'assert', 'del'):
                continue

            # Module-level variables should be UPPER_SNAKE or snake_case
            if not indent.strip():  # Module level
                if name.isupper() or self.UPPER_SNAKE.match(name):
                    continue  # Constants are fine

            # Check for single letter variables (except common loop vars)
            if len(name) == 1 and name not in ('i', 'j', 'k', 'x', 'y', 'z', 'e', 'f',
                                                 'n', 'm', 'a', 'b', 'v', 't'):
                findings.append({
                    "severity": "info",
                    "category": "naming_readability",
                    "message": f"Single-letter variable '{name}' reduces readability",
                    "line_start": line_num,
                    "suggestion": "Use a descriptive name that conveys the variable's purpose",
                    "confidence": 0.7
                })

        return findings[:10]  # Limit findings

    def _check_constant_names(self, code: str) -> List[Dict]:
        """Check constant naming conventions."""
        findings = []
        # Find module-level assignments that look like constants
        for match in re.finditer(r'^([A-Z][A-Za-z0-9]*)\s*=', code, re.MULTILINE):
            name = match.group(1)
            line_num = code[:match.start()].count('\n') + 1

            # Constants should be UPPER_SNAKE_CASE
            if not self.UPPER_SNAKE.match(name) and not name.startswith('_'):
                if self.PASCAL_CASE.match(name):
                    findings.append({
                        "severity": "info",
                        "category": "naming_convention",
                        "message": f"Possible constant '{name}' should be UPPER_SNAKE_CASE",
                        "line_start": line_num,
                        "suggestion": f"Rename to '{self._to_upper_snake(name)}'",
                        "confidence": 0.7
                    })

        return findings

    def _check_parameter_names(self, code: str) -> List[Dict]:
        """Check function parameter naming."""
        findings = []
        for match in re.finditer(r'def\s+\w+\s*\(([^)]+)\)', code):
            params_str = match.group(1)
            line_num = code[:match.start()].count('\n') + 1

            params = [p.strip().split(':')[0].strip().split('=')[0].strip()
                     for p in params_str.split(',') if p.strip() and p.strip() != 'self']

            for param in params:
                if param.startswith('**') or param.startswith('*'):
                    param = param.lstrip('*')
                if len(param) == 1 and param not in ('i', 'j', 'k', 'x', 'y'):
                    findings.append({
                        "severity": "info",
                        "category": "naming_readability",
                        "message": f"Single-letter parameter '{param}' in function definition",
                        "line_start": line_num,
                        "confidence": 0.75
                    })

        return findings[:5]

    def _check_name_lengths(self, code: str) -> List[Dict]:
        """Check for excessively long or short names."""
        findings = []
        all_names = re.findall(r'\b([a-zA-Z_]\w{30,})\b', code)

        for name in set(all_names):
            if len(name) > 40:
                findings.append({
                    "severity": "info",
                    "category": "naming_readability",
                    "message": f"Very long name '{name}' ({len(name)} chars)",
                    "suggestion": "Consider a shorter but still descriptive name",
                    "confidence": 0.7
                })

        return findings[:5]

    def _check_abbreviations(self, code: str) -> List[Dict]:
        """Check for unclear abbreviations."""
        findings = []
        found_abbrs = set()

        for match in re.finditer(r'\b([a-z]{2,5})\b', code):
            word = match.group(1)
            if word in self.BAD_ABBREVIATIONS and word not in found_abbrs:
                found_abbrs.add(word)

        # Only report if many abbreviations are used
        if len(found_abbrs) > 5:
            findings.append({
                "severity": "info",
                "category": "naming_readability",
                "message": f"Found {len(found_abbrs)} common abbreviations that may reduce readability",
                "suggestion": f"Consider expanding: {', '.join(sorted(found_abbrs)[:8])}",
                "confidence": 0.6
            })

        return findings

    def _extract_all_names(self, code: str) -> List[Dict]:
        """Extract all named entities from code."""
        names = []

        # Functions
        for match in re.finditer(r'def\s+(\w+)', code):
            names.append({"name": match.group(1), "type": "function",
                         "line": code[:match.start()].count('\n') + 1})

        # Classes
        for match in re.finditer(r'class\s+(\w+)', code):
            names.append({"name": match.group(1), "type": "class",
                         "line": code[:match.start()].count('\n') + 1})

        # Variables (assignments)
        for match in re.finditer(r'([a-zA-Z_]\w*)\s*=(?!=)', code):
            name = match.group(1)
            if name not in ('self', 'cls', 'def', 'class', 'import', 'from', 'return',
                           'if', 'else', 'for', 'while', 'try', 'except'):
                names.append({"name": name, "type": "variable",
                             "line": code[:match.start()].count('\n') + 1})

        return names

    def _calculate_naming_stats(self, names: List[Dict]) -> Dict:
        """Calculate naming style distribution."""
        stats = {"snake_case": 0, "camelCase": 0, "PascalCase": 0,
                "UPPER_SNAKE": 0, "other": 0}

        for name_info in names:
            name = name_info["name"]
            if self.SNAKE_CASE.match(name):
                stats["snake_case"] += 1
            elif self.UPPER_SNAKE.match(name):
                stats["UPPER_SNAKE"] += 1
            elif self.PASCAL_CASE.match(name):
                stats["PascalCase"] += 1
            elif self.CAMEL_CASE.match(name):
                stats["camelCase"] += 1
            else:
                stats["other"] += 1

        return stats

    def _analyze_consistency(self, code: str) -> Dict:
        """Analyze naming consistency across the codebase."""
        # Track naming patterns per context
        function_names = [m.group(1) for m in re.finditer(r'def\s+(\w+)', code)]
        class_names = [m.group(1) for m in re.finditer(r'class\s+(\w+)', code)]

        # Check consistency within functions
        func_styles = defaultdict(int)
        for name in function_names:
            if name.startswith('__') and name.endswith('__'):
                continue
            clean_name = name.lstrip('_')
            if self.SNAKE_CASE.match(clean_name):
                func_styles["snake_case"] += 1
            elif self.CAMEL_CASE.match(clean_name):
                func_styles["camelCase"] += 1
            else:
                func_styles["other"] += 1

        # Check consistency within classes
        class_styles = defaultdict(int)
        for name in class_names:
            if self.PASCAL_CASE.match(name):
                class_styles["PascalCase"] += 1
            elif self.SNAKE_CASE.match(name):
                class_styles["snake_case"] += 1
            else:
                class_styles["other"] += 1

        # Calculate consistency score
        total_funcs = sum(func_styles.values())
        total_classes = sum(class_styles.values())

        func_consistency = max(func_styles.values()) / max(1, total_funcs) * 100 if func_styles else 100
        class_consistency = max(class_styles.values()) / max(1, total_classes) * 100 if class_styles else 100

        overall_consistency = (func_consistency + class_consistency) / 2

        return {
            "score": round(overall_consistency, 1),
            "function_style_distribution": dict(func_styles),
            "class_style_distribution": dict(class_styles),
            "function_consistency": round(func_consistency, 1),
            "class_consistency": round(class_consistency, 1)
        }

    def _to_snake_case(self, name: str) -> str:
        """Convert a name to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_pascal_case(self, name: str) -> str:
        """Convert a name to PascalCase."""
        return ''.join(word.capitalize() for word in name.split('_'))

    def _to_upper_snake(self, name: str) -> str:
        """Convert a name to UPPER_SNAKE_CASE."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper()

    def _calculate_score(self, findings: List[Dict], all_names: List[Dict],
                        consistency: Dict) -> float:
        """Calculate naming convention score (0-100)."""
        if not all_names:
            return 100.0

        score = 100.0

        # Penalize based on findings
        severity_penalties = {"error": 5, "warning": 3, "info": 1}
        for finding in findings:
            score -= severity_penalties.get(finding["severity"], 1)

        # Factor in consistency
        consistency_factor = consistency["score"] / 100
        score = score * 0.7 + (consistency_factor * 100) * 0.3

        return max(0, min(100, round(score, 1)))
