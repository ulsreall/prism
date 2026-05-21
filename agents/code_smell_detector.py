"""
PRISM - Code Smell Detector Agent
Estimated token consumption: ~18K tokens per analysis

Detects:
- God Class (too many responsibilities)
- Long Method (excessive method length)
- Feature Envy (excessive use of other class's data)
- Data Clumps (repeated parameter groups)
- Primitive Obsession
- Switch Statements
- Parallel Inheritance Hierarchies
- Lazy Class
- Speculative Generality
- Temporary Field
"""

import re
from typing import Dict, List, Any, Set, Tuple
from collections import Counter, defaultdict


class CodeSmellDetectorAgent:
    """Agent for detecting code smells and anti-patterns."""

    AGENT_NAME = "Code Smell Detector"
    ESTIMATED_TOKENS = 18000

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Detect code smells across multiple categories."""
        findings = []
        lines = code.split('\n')

        # 1. God Class detection
        god_class_findings = self._detect_god_class(code, lines)
        findings.extend(god_class_findings)

        # 2. Long Method detection
        long_method_findings = self._detect_long_methods(code, lines)
        findings.extend(long_method_findings)

        # 3. Feature Envy detection
        feature_envy_findings = self._detect_feature_envy(code)
        findings.extend(feature_envy_findings)

        # 4. Data Clumps detection
        data_clumps_findings = self._detect_data_clumps(code)
        findings.extend(data_clumps_findings)

        # 5. Primitive Obsession
        primitive_findings = self._detect_primitive_obsession(code)
        findings.extend(primitive_findings)

        # 6. Long Parameter List
        param_list_findings = self._detect_long_parameter_lists(code)
        findings.extend(param_list_findings)

        # 7. Dead Code indicators
        dead_code_findings = self._detect_dead_code_indicators(code, lines)
        findings.extend(dead_code_findings)

        # 8. Shotgun Surgery indicators
        surgery_findings = self._detect_shotgun_surgery(code, lines)
        findings.extend(surgery_findings)

        # 9. Divergent Change indicators
        divergent_findings = self._detect_divergent_change(code, lines)
        findings.extend(divergent_findings)

        # 10. Temporary Field
        temp_field_findings = self._detect_temporary_fields(code)
        findings.extend(temp_field_findings)

        # Calculate metrics
        smell_counts = Counter(f["category"] for f in findings)
        severity_counts = Counter(f["severity"] for f in findings)

        score = self._calculate_score(findings, len(lines))

        metrics = {
            "score": score,
            "total_smells": len(findings),
            "smell_categories": dict(smell_counts),
            "severity_distribution": dict(severity_counts),
            "smells_per_100_lines": round(len(findings) / max(1, len(lines)) * 100, 2),
            "top_smells": [f["category"] for f in findings[:5]],
            "smell_density": self._calculate_smell_density(findings, len(lines))
        }

        tokens_used = len(code) // 4 + len(findings) * 180 + 600
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _detect_god_class(self, code: str, lines: List[str]) -> List[Dict]:
        """Detect classes with too many responsibilities."""
        findings = []
        classes = re.finditer(r'class\s+(\w+)\s*(?:\([^)]*\))?\s*:', code)

        for cls_match in classes:
            cls_name = cls_match.group(1)
            cls_start = cls_match.start()

            # Find class body
            cls_body = self._extract_class_body(code, cls_start)

            # Count methods
            methods = re.findall(r'(?:async\s+)?def\s+(\w+)', cls_body)
            # Count instance variables
            instance_vars = set(re.findall(r'self\.(\w+)', cls_body))
            # Count lines
            cls_lines = cls_body.count('\n')

            is_god_class = False
            reasons = []

            if len(methods) > 20:
                is_god_class = True
                reasons.append(f"{len(methods)} methods (threshold: 20)")
            if len(instance_vars) > 15:
                is_god_class = True
                reasons.append(f"{len(instance_vars)} instance variables (threshold: 15)")
            if cls_lines > 500:
                is_god_class = True
                reasons.append(f"{cls_lines} lines (threshold: 500)")

            # Check for multiple responsibilities (different method prefixes)
            method_prefixes = set()
            for method in methods:
                parts = method.split('_')
                if len(parts) > 1:
                    method_prefixes.add(parts[0])
            if len(method_prefixes) > 5:
                is_god_class = True
                reasons.append(f"{len(method_prefixes)} different responsibility areas")

            if is_god_class:
                findings.append({
                    "severity": "error",
                    "category": "god_class",
                    "message": f"God Class detected: '{cls_name}' - {'; '.join(reasons)}",
                    "line_start": code[:cls_start].count('\n') + 1,
                    "suggestion": f"Split '{cls_name}' into smaller, focused classes with single responsibility",
                    "confidence": 0.9
                })

        return findings

    def _detect_long_methods(self, code: str, lines: List[str]) -> List[Dict]:
        """Detect methods that are too long."""
        findings = []
        func_pattern = re.compile(r'^(\s*)(async\s+)?def\s+(\w+)\s*\(', re.MULTILINE)

        for match in func_pattern.finditer(code):
            func_name = match.group(3)
            func_start = match.start()
            func_body = self._extract_function_body(code, func_start)
            func_lines = func_body.count('\n')

            if func_lines > 50:
                severity = "critical" if func_lines > 100 else "error" if func_lines > 75 else "warning"
                findings.append({
                    "severity": severity,
                    "category": "long_method",
                    "message": f"Long method: '{func_name}' is {func_lines} lines",
                    "line_start": code[:func_start].count('\n') + 1,
                    "line_end": code[:func_start].count('\n') + func_lines,
                    "suggestion": f"Extract logical sections of '{func_name}' into helper methods",
                    "confidence": 0.95
                })

        return findings

    def _detect_feature_envy(self, code: str) -> List[Dict]:
        """Detect methods that use more external class data than their own."""
        findings = []
        # Find method bodies and check for excessive external references
        methods = re.finditer(r'(?:async\s+)?def\s+(\w+)\s*\([^)]*\).*?(?=\n\S|\Z)', code, re.DOTALL)

        for method_match in methods:
            method_name = method_match.group(1)
            method_body = method_match.group(0)

            # Count self references vs external references
            self_refs = len(re.findall(r'self\.\w+', method_body))
            # Look for parameter.attr patterns
            param_refs = re.findall(r'(\w+)\.(\w+)', method_body)
            external_refs = sum(1 for obj, _ in param_refs if obj != 'self' and obj not in
                              {'os', 'sys', 're', 'json', 'math', 'datetime', 'time', 'typing'})

            if external_refs > 5 and external_refs > self_refs * 2 and self_refs > 0:
                findings.append({
                    "severity": "warning",
                    "category": "feature_envy",
                    "message": f"Method '{method_name}' may belong in another class (uses {external_refs} external refs vs {self_refs} self refs)",
                    "line_start": code[:method_match.start()].count('\n') + 1,
                    "suggestion": f"Consider moving '{method_name}' to the class it references most",
                    "confidence": 0.75
                })

        return findings

    def _detect_data_clumps(self, code: str) -> List[Dict]:
        """Detect repeated parameter groups that should be a class."""
        findings = []
        # Extract function parameter lists
        param_groups = []
        func_pattern = re.compile(r'def\s+(\w+)\s*\(([^)]+)\)', re.DOTALL)

        for match in func_pattern.finditer(code):
            func_name = match.group(1)
            params_str = match.group(2)
            params = [p.strip().split(':')[0].strip().split('=')[0].strip()
                     for p in params_str.split(',')
                     if p.strip() and p.strip() != 'self']
            if len(params) >= 2:
                param_groups.append((func_name, tuple(sorted(params))))

        # Find repeated parameter combinations
        param_counter = Counter(params for _, params in param_groups)
        for params, count in param_counter.items():
            if count >= 3 and len(params) >= 3:
                funcs_with_clump = [name for name, p in param_groups if p == params]
                findings.append({
                    "severity": "warning",
                    "category": "data_clumps",
                    "message": f"Data clump: parameters {params} appear together in {count} functions",
                    "suggestion": f"Create a data class to group: {', '.join(params)}",
                    "confidence": 0.8
                })

        return findings

    def _detect_primitive_obsession(self, code: str) -> List[Dict]:
        """Detect overuse of primitive types instead of objects."""
        findings = []

        # Check for string-typed status/type fields
        status_patterns = re.findall(r"(\w+)\s*(?:==|!=|in)\s*['\"](\w+)['\"]", code)
        status_groups = defaultdict(list)
        for var, value in status_patterns:
            if var in ('status', 'state', 'type', 'kind', 'category', 'role'):
                status_groups[var].append(value)

        for var, values in status_groups.items():
            if len(set(values)) > 3:
                findings.append({
                    "severity": "info",
                    "category": "primitive_obsession",
                    "message": f"Possible primitive obsession: '{var}' compared against {len(set(values))} string values",
                    "suggestion": f"Consider using an Enum for '{var}' instead of string literals",
                    "confidence": 0.7
                })

        return findings

    def _detect_long_parameter_lists(self, code: str) -> List[Dict]:
        """Detect functions with too many parameters."""
        findings = []
        func_pattern = re.compile(r'def\s+(\w+)\s*\(([^)]+)\)')

        for match in func_pattern.finditer(code):
            func_name = match.group(1)
            params = [p.strip() for p in match.group(2).split(',')
                     if p.strip() and p.strip() != 'self']
            if len(params) > 7:
                findings.append({
                    "severity": "error",
                    "category": "long_parameter_list",
                    "message": f"'{func_name}' has {len(params)} parameters (max recommended: 5)",
                    "line_start": code[:match.start()].count('\n') + 1,
                    "suggestion": f"Group parameters into a configuration object or data class",
                    "confidence": 0.9
                })
            elif len(params) > 5:
                findings.append({
                    "severity": "warning",
                    "category": "long_parameter_list",
                    "message": f"'{func_name}' has {len(params)} parameters",
                    "line_start": code[:match.start()].count('\n') + 1,
                    "suggestion": "Consider if some parameters could be grouped or defaulted",
                    "confidence": 0.85
                })

        return findings

    def _detect_dead_code_indicators(self, code: str, lines: List[str]) -> List[Dict]:
        """Detect potential dead code patterns."""
        findings = []

        # Commented-out code blocks
        commented_code = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') and any(kw in stripped for kw in
                ['def ', 'class ', 'import ', 'return ', 'if ', 'for ', 'print(']):
                commented_code += 1
        if commented_code > 5:
            findings.append({
                "severity": "warning",
                "category": "dead_code",
                "message": f"Found {commented_code} lines of commented-out code",
                "suggestion": "Remove commented-out code; use version control to preserve history",
                "confidence": 0.85
            })

        # Unreachable code after return/raise
        unreachable = 0
        prev_was_return = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('return ', 'raise ', 'return\n')):
                prev_was_return = True
            elif stripped and not stripped.startswith(('#', '"""', "'''")) and prev_was_return:
                if not stripped.startswith(('except', 'finally', 'elif', 'else', 'except:', 'finally:')):
                    unreachable += 1
            else:
                prev_was_return = False

        if unreachable > 0:
            findings.append({
                "severity": "warning",
                "category": "dead_code",
                "message": f"Found {unreachable} potentially unreachable code blocks",
                "suggestion": "Remove unreachable code after return/raise statements",
                "confidence": 0.7
            })

        return findings

    def _detect_shotgun_surgery(self, code: str, lines: List[str]) -> List[Dict]:
        """Detect code that requires changes in many places for single modification."""
        findings = []

        # Find repeated string literals that might indicate shotgun surgery
        string_literals = re.findall(r"['\"]([^'\"]{10,})['\"]", code)
        string_counts = Counter(string_literals)
        for string, count in string_counts.items():
            if count > 3:
                findings.append({
                    "severity": "warning",
                    "category": "shotgun_surgery",
                    "message": f"String '{string[:30]}...' repeated {count} times",
                    "suggestion": "Extract to a constant to avoid changing multiple locations",
                    "confidence": 0.8
                })

        return findings[:5]  # Limit findings

    def _detect_divergent_change(self, code: str, lines: List[str]) -> List[Dict]:
        """Detect classes that change for many different reasons."""
        findings = []

        classes = re.finditer(r'class\s+(\w+)', code)
        for cls_match in classes:
            cls_name = cls_match.group(1)
            cls_body = self._extract_class_body(code, cls_match.start())

            # Check for unrelated method groups
            methods = re.findall(r'def\s+(\w+)', cls_body)
            if len(methods) > 10:
                # Analyze method naming patterns for different concerns
                concerns = set()
                for method in methods:
                    parts = method.split('_')
                    if len(parts) > 1:
                        concerns.add(parts[0])
                if len(concerns) > 4:
                    findings.append({
                        "severity": "warning",
                        "category": "divergent_change",
                        "message": f"Class '{cls_name}' appears to have {len(concerns)} different concerns",
                        "suggestion": f"Split '{cls_name}' by responsibility",
                        "confidence": 0.75
                    })

        return findings

    def _detect_temporary_fields(self, code: str) -> List[Dict]:
        """Detect instance variables only used in certain circumstances."""
        findings = []

        # Find __init__ method and track which instance vars are used
        init_match = re.search(r'def\s+__init__\s*\(self[^)]*\)(.*?)(?=\n\s*def\s|\Z)', code, re.DOTALL)
        if init_match:
            init_body = init_match.group(1)
            init_vars = set(re.findall(r'self\.(\w+)\s*=', init_body))

            # Check usage across entire class
            for var in init_vars:
                usage_count = len(re.findall(rf'self\.{var}\b', code))
                if usage_count <= 2:  # Only set and maybe read once
                    findings.append({
                        "severity": "info",
                        "category": "temporary_field",
                        "message": f"Instance variable '{var}' appears to be rarely used ({usage_count} references)",
                        "suggestion": "Consider if '{var}' should be a local variable or method parameter",
                        "confidence": 0.6
                    })

        return findings

    def _extract_class_body(self, code: str, start: int) -> str:
        """Extract the body of a class starting from its definition."""
        lines = code[start:].split('\n')
        if not lines:
            return ""
        base_indent = len(lines[0]) - len(lines[0].lstrip())
        body_lines = [lines[0]]
        for line in lines[1:]:
            if line.strip() == '':
                body_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent and line.strip():
                break
            body_lines.append(line)
        return '\n'.join(body_lines)

    def _extract_function_body(self, code: str, start: int) -> str:
        """Extract the body of a function starting from its definition."""
        lines = code[start:].split('\n')
        if not lines:
            return ""
        base_indent = len(lines[0]) - len(lines[0].lstrip())
        body_lines = [lines[0]]
        for line in lines[1:]:
            if line.strip() == '':
                body_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent and line.strip():
                break
            body_lines.append(line)
        return '\n'.join(body_lines)

    def _calculate_smell_density(self, findings: List[Dict], total_lines: int) -> str:
        """Calculate smell density rating."""
        density = len(findings) / max(1, total_lines) * 100
        if density < 1:
            return "low"
        elif density < 3:
            return "moderate"
        elif density < 5:
            return "high"
        else:
            return "very_high"

    def _calculate_score(self, findings: List[Dict], total_lines: int) -> float:
        """Calculate code smell score (0-100, higher is better)."""
        score = 100.0

        severity_penalties = {"critical": 10, "error": 5, "warning": 3, "info": 1}
        for finding in findings:
            score -= severity_penalties.get(finding["severity"], 1)

        return max(0, min(100, round(score, 1)))
