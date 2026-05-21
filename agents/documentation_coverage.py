"""
PRISM - Documentation Coverage Agent
Estimated token consumption: ~14K tokens per analysis

Analyzes:
- Docstring coverage for classes and functions
- Module-level documentation
- Comment density and quality
- API documentation completeness
- Type hint coverage
- README/documentation file presence
"""

import re
from typing import Dict, List, Any, Tuple
from collections import defaultdict


class DocumentationCoverageAgent:
    """Agent for analyzing documentation coverage and quality."""

    AGENT_NAME = "Documentation Coverage"
    ESTIMATED_TOKENS = 14000

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Analyze documentation coverage across the codebase."""
        findings = []
        lines = code.split('\n')

        # 1. Module documentation
        module_doc = self._check_module_documentation(code)
        if not module_doc["has_docstring"]:
            findings.append({
                "severity": "warning",
                "category": "module_documentation",
                "message": "Module is missing a docstring",
                "line_start": 1,
                "suggestion": "Add a module-level docstring describing the purpose and contents",
                "confidence": 0.9
            })

        # 2. Class documentation
        class_doc_findings = self._check_class_documentation(code)
        findings.extend(class_doc_findings)

        # 3. Function/method documentation
        func_doc_findings = self._check_function_documentation(code)
        findings.extend(func_doc_findings)

        # 4. Comment density
        comment_metrics = self._analyze_comment_density(lines)

        # 5. Type hint coverage
        type_hint_findings = self._check_type_hints(code)
        findings.extend(type_hint_findings)

        # 6. TODO/FIXME tracking
        todo_findings = self._check_todos(code, lines)
        findings.extend(todo_findings)

        # 7. Complex code without comments
        complexity_comment_findings = self._check_complex_code_comments(code, lines)
        findings.extend(complexity_comment_findings)

        # Calculate metrics
        all_entities = self._count_documentable_entities(code)
        documented_entities = self._count_documented_entities(code)
        coverage_pct = documented_entities / max(1, all_entities) * 100

        score = self._calculate_score(coverage_pct, comment_metrics, len(findings))

        metrics = {
            "score": score,
            "documentation_coverage": round(coverage_pct, 1),
            "module_documented": module_doc["has_docstring"],
            "total_documentable_entities": all_entities,
            "documented_entities": documented_entities,
            "undocumented_entities": all_entities - documented_entities,
            "comment_density": comment_metrics["density"],
            "comment_ratio": comment_metrics["ratio"],
            "type_hint_coverage": self._calculate_type_hint_coverage(code),
            "todo_count": len(todo_findings),
            "comment_quality_score": comment_metrics["quality_score"]
        }

        tokens_used = len(code) // 4 + len(findings) * 120 + 400
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _check_module_documentation(self, code: str) -> Dict:
        """Check if module has a docstring."""
        stripped = code.strip()
        has_docstring = False

        if stripped.startswith('"""') or stripped.startswith("'''"):
            has_docstring = True
        elif stripped.startswith('#'):
            # Check if there's a docstring after comments
            lines = stripped.split('\n')
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith('#'):
                    continue
                if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                    has_docstring = True
                break

        return {"has_docstring": has_docstring}

    def _check_class_documentation(self, code: str) -> List[Dict]:
        """Check documentation for all classes."""
        findings = []
        classes = list(re.finditer(r'class\s+(\w+)(?:\([^)]*\))?\s*:', code))

        for cls_match in classes:
            cls_name = cls_match.group(1)
            cls_start = cls_match.end()
            line_num = code[:cls_match.start()].count('\n') + 1

            # Check if class has a docstring
            after_class = code[cls_start:].lstrip()
            if not (after_class.startswith('"""') or after_class.startswith("'''")):
                findings.append({
                    "severity": "warning",
                    "category": "class_documentation",
                    "message": f"Class '{cls_name}' is missing a docstring",
                    "line_start": line_num,
                    "suggestion": f"Add a docstring to '{cls_name}' explaining its purpose and usage",
                    "confidence": 0.9
                })

        return findings

    def _check_function_documentation(self, code: str) -> List[Dict]:
        """Check documentation for all functions/methods."""
        findings = []
        func_pattern = re.compile(r'(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->.*?)?:')

        for func_match in func_pattern.finditer(code):
            func_name = func_match.group(1)
            func_end = func_match.end()
            line_num = code[:func_match.start()].count('\n') + 1

            # Skip dunder methods (except __init__)
            if func_name.startswith('__') and func_name.endswith('__') and func_name != '__init__':
                continue

            # Check if function has a docstring
            after_func = code[func_end:].lstrip()
            has_docstring = after_func.startswith('"""') or after_func.startswith("'''")

            if not has_docstring:
                severity = "warning" if not func_name.startswith('_') else "info"
                findings.append({
                    "severity": severity,
                    "category": "function_documentation",
                    "message": f"Function '{func_name}' is missing a docstring",
                    "line_start": line_num,
                    "suggestion": f"Add a docstring to '{func_name}' describing parameters, return value, and purpose",
                    "confidence": 0.9
                })
            else:
                # Check docstring quality
                doc_match = re.match(r'("""|\'\'\')(.*?)(\1)', after_func, re.DOTALL)
                if doc_match:
                    docstring = doc_match.group(2).strip()
                    quality_issues = self._assess_docstring_quality(docstring, func_name)
                    for issue in quality_issues:
                        findings.append({
                            "severity": "info",
                            "category": "docstring_quality",
                            "message": f"Docstring for '{func_name}': {issue}",
                            "line_start": line_num,
                            "confidence": 0.7
                        })

        return findings[:15]  # Limit findings

    def _assess_docstring_quality(self, docstring: str, func_name: str) -> List[str]:
        """Assess the quality of a docstring."""
        issues = []

        if len(docstring) < 10:
            issues.append("Docstring is too short to be useful")

        # Check for parameter documentation
        has_params = bool(re.search(r'(Args|Parameters|Params|:param)\s*:', docstring, re.IGNORECASE))
        has_returns = bool(re.search(r'(Returns|Return|:returns|:return)\s*:', docstring, re.IGNORECASE))
        has_raises = bool(re.search(r'(Raises|Throws|:raises)\s*:', docstring, re.IGNORECASE))

        if not has_params and '(' in func_name:
            # Function likely has params
            issues.append("Missing parameter documentation (Args section)")

        if not has_returns:
            issues.append("Missing return value documentation")

        return issues

    def _analyze_comment_density(self, lines: List[str]) -> Dict:
        """Analyze comment density and quality."""
        total_lines = len(lines)
        code_lines = 0
        comment_lines = 0
        inline_comments = 0
        block_comments = 0
        in_multiline = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if '"""' in stripped or "'''" in stripped:
                count = stripped.count('"""') + stripped.count("'''")
                if count == 2:
                    # Single line docstring
                    comment_lines += 1
                elif count == 1:
                    in_multiline = not in_multiline
                    comment_lines += 1
                continue

            if in_multiline:
                comment_lines += 1
                continue

            if stripped.startswith('#'):
                comment_lines += 1
            elif '#' in stripped:
                code_lines += 1
                inline_comments += 1
            else:
                code_lines += 1

        density = comment_lines / max(1, total_lines) * 100
        ratio = comment_lines / max(1, code_lines) * 100

        # Quality score based on density
        if density < 5:
            quality_score = 30
        elif density < 10:
            quality_score = 50
        elif density < 20:
            quality_score = 75
        elif density < 40:
            quality_score = 90
        else:
            quality_score = 70  # Too many comments can be noise

        return {
            "density": round(density, 1),
            "ratio": round(ratio, 1),
            "comment_lines": comment_lines,
            "code_lines": code_lines,
            "inline_comments": inline_comments,
            "quality_score": quality_score
        }

    def _check_type_hints(self, code: str) -> List[Dict]:
        """Check type hint coverage."""
        findings = []

        # Find function definitions with and without type hints
        func_pattern = re.compile(r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*\w+)?:')
        functions = list(func_pattern.finditer(code))

        if not functions:
            return findings

        with_hints = 0
        without_hints = 0

        for func_match in functions:
            func_name = func_match.group(1)
            params = func_match.group(2)
            full_match = func_match.group(0)

            # Check return type hint
            has_return_hint = '->' in full_match

            # Check parameter type hints
            param_hints = len(re.findall(r':\s*\w+', params))
            total_params = len([p.strip() for p in params.split(',')
                              if p.strip() and p.strip() != 'self'])

            if has_return_hint and (total_params == 0 or param_hints >= total_params):
                with_hints += 1
            else:
                without_hints += 1
                if not func_name.startswith('_'):
                    findings.append({
                        "severity": "info",
                        "category": "type_hints",
                        "message": f"Function '{func_name}' is missing type hints",
                        "line_start": code[:func_match.start()].count('\n') + 1,
                        "suggestion": f"Add type annotations to '{func_name}' for better IDE support and documentation",
                        "confidence": 0.8
                    })

        return findings[:10]

    def _check_todos(self, code: str, lines: List[str]) -> List[Dict]:
        """Find TODO/FIXME/HACK comments."""
        findings = []

        for i, line in enumerate(lines):
            for pattern, severity in [
                (r'#\s*FIXME', "warning"),
                (r'#\s*HACK', "warning"),
                (r'#\s*XXX', "warning"),
                (r'#\s*TODO', "info"),
                (r'#\s*NOTE', "info"),
            ]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    findings.append({
                        "severity": severity,
                        "category": "todo_marker",
                        "message": f"{match.group().strip()} at line {i+1}: {line.strip()[:60]}",
                        "line_start": i + 1,
                        "suggestion": "Track TODO items in issue tracker and resolve them",
                        "confidence": 0.9
                    })

        return findings[:10]

    def _check_complex_code_comments(self, code: str, lines: List[str]) -> List[Dict]:
        """Check if complex code sections have explanatory comments."""
        findings = []

        # Find complex expressions without comments
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Check for complex regex patterns
            if re.search(r're\.compile\(|re\.\w+\(', stripped):
                # Check if there's a comment on this or previous line
                has_comment = False
                if '#' in stripped:
                    has_comment = True
                elif i > 0 and lines[i-1].strip().startswith('#'):
                    has_comment = True
                if not has_comment:
                    findings.append({
                        "severity": "info",
                        "category": "missing_comment",
                        "message": f"Complex regex at line {i+1} lacks explanatory comment",
                        "line_start": i + 1,
                        "suggestion": "Add a comment explaining what the regex matches",
                        "confidence": 0.7
                    })

        return findings[:5]

    def _count_documentable_entities(self, code: str) -> int:
        """Count total documentable entities."""
        classes = len(re.findall(r'class\s+\w+', code))
        functions = len(re.findall(r'(?:async\s+)?def\s+\w+', code))
        return classes + functions + 1  # +1 for module

    def _count_documented_entities(self, code: str) -> int:
        """Count documented entities."""
        documented = 0

        # Module
        if code.strip().startswith(('"""', "'''", '#')):
            documented += 1

        # Check each class/function for docstring
        pattern = re.compile(r'(?:class\s+\w+|(?:async\s+)?def\s+\w+)[^:]*:')
        for match in pattern.finditer(code):
            after = code[match.end():].lstrip()
            if after.startswith(('"""', "'''")):
                documented += 1

        return documented

    def _calculate_type_hint_coverage(self, code: str) -> float:
        """Calculate type hint coverage percentage."""
        func_pattern = re.compile(r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*[\w\[\], ]+)?:')
        functions = list(func_pattern.finditer(code))

        if not functions:
            return 100.0

        with_hints = 0
        for func_match in functions:
            full_match = func_match.group(0)
            if '->' in full_match:
                with_hints += 1

        return round(with_hints / len(functions) * 100, 1)

    def _calculate_score(self, coverage_pct: float, comment_metrics: Dict,
                        finding_count: int) -> float:
        """Calculate documentation score (0-100)."""
        # Coverage component (40% weight)
        coverage_score = min(100, coverage_pct * 1.2)

        # Comment density component (30% weight)
        density_score = comment_metrics["quality_score"]

        # Finding penalty (30% weight)
        finding_penalty = max(0, 100 - finding_count * 3)

        score = coverage_score * 0.4 + density_score * 0.3 + finding_penalty * 0.3
        return max(0, min(100, round(score, 1)))
