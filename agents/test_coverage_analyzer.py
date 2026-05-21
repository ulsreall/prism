"""
PRISM - Test Coverage Analyzer Agent
Estimated token consumption: ~16K tokens per analysis

Analyzes:
- Test function presence and naming
- Assertion density and variety
- Edge case coverage
- Test isolation patterns
- Mock/patch usage
- Test documentation
- Parameterized test usage
"""

import re
from typing import Dict, List, Any
from collections import defaultdict


class TestCoverageAnalyzerAgent:
    """Agent for analyzing test coverage patterns and quality."""

    AGENT_NAME = "Test Coverage Analyzer"
    ESTIMATED_TOKENS = 16000

    # Test function naming patterns
    TEST_PATTERNS = [
        r'def\s+(test_\w+)',
        r'def\s+(it_\w+)',
        r'def\s+(should_\w+)',
        r'class\s+(Test\w+)',
        r'class\s+(.*Test\b)',
    ]

    # Assertion patterns
    ASSERTION_PATTERNS = [
        r'\bassert\b',
        r'\bassertEqual\b',
        r'\bassertNotEqual\b',
        r'\bassertTrue\b',
        r'\bassertFalse\b',
        r'\bassertIs\b',
        r'\bassertIsNone\b',
        r'\bassertIsNotNone\b',
        r'\bassertIn\b',
        r'\bassertNotIn\b',
        r'\bassertRaises\b',
        r'\bassertWarns\b',
        r'\bassertAlmostEqual\b',
        r'\bassertGreater\b',
        r'\bassertLess\b',
        r'\bassertContains\b',
        r'\bassert_status_code\b',
        r'\bexpect\b',
        r'\bshould\b',
        r'\bmust\b',
        r'\bpytest\.raises\b',
    ]

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Analyze test coverage patterns and quality."""
        findings = []
        is_test_file = self._is_test_file(context.get("file_path", ""), code)

        # 1. Check for test functions
        test_functions = self._find_test_functions(code)
        all_functions = self._find_all_functions(code)

        if not is_test_file and not test_functions:
            findings.append({
                "severity": "warning",
                "category": "test_presence",
                "message": "No test functions found in this file",
                "suggestion": "Add test functions to verify the behavior of your code",
                "confidence": 0.8
            })

        # 2. Analyze test function quality
        test_quality = self._analyze_test_quality(test_functions, code)
        findings.extend(test_quality["findings"])

        # 3. Assertion analysis
        assertion_analysis = self._analyze_assertions(code, test_functions)
        findings.extend(assertion_analysis["findings"])

        # 4. Test isolation
        isolation_findings = self._check_test_isolation(code, test_functions)
        findings.extend(isolation_findings)

        # 5. Edge case coverage
        edge_case_findings = self._check_edge_cases(code, test_functions)
        findings.extend(edge_case_findings)

        # 6. Mock usage
        mock_findings = self._check_mock_usage(code, test_functions)
        findings.extend(mock_findings)

        # 7. Test documentation
        doc_findings = self._check_test_documentation(test_functions, code)
        findings.extend(doc_findings)

        # 8. Test naming quality
        naming_findings = self._check_test_naming(test_functions)
        findings.extend(naming_findings)

        # Calculate metrics
        test_ratio = len(test_functions) / max(1, len(all_functions)) * 100
        assertion_density = assertion_analysis["total_assertions"] / max(1, len(test_functions))

        score = self._calculate_score(
            test_ratio, assertion_density, len(findings), test_quality
        )

        metrics = {
            "score": score,
            "is_test_file": is_test_file,
            "test_function_count": len(test_functions),
            "total_function_count": len(all_functions),
            "test_ratio": round(test_ratio, 1),
            "assertion_count": assertion_analysis["total_assertions"],
            "assertion_density": round(assertion_density, 2),
            "assertion_types": assertion_analysis["assertion_types"],
            "test_quality": test_quality["summary"],
            "edge_cases_found": edge_case_findings.__len__(),
            "has_mocks": len(mock_findings) > 0,
            "test_naming_score": naming_findings.__len__()
        }

        tokens_used = len(code) // 4 + len(findings) * 150 + 500
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _is_test_file(self, file_path: str, code: str) -> bool:
        """Determine if this is a test file."""
        test_indicators = ['test_', '_test.py', 'tests/', 'test/', 'spec_', '_spec.']
        path_match = any(indicator in file_path.lower() for indicator in test_indicators)

        # Also check content
        content_match = bool(re.search(r'(import\s+pytest|import\s+unittest|from\s+unittest)', code))

        return path_match or content_match

    def _find_test_functions(self, code: str) -> List[Dict]:
        """Find all test functions in the code."""
        tests = []
        for pattern in self.TEST_PATTERNS:
            for match in re.finditer(pattern, code):
                name = match.group(1)
                line_num = code[:match.start()].count('\n') + 1
                is_class = pattern.startswith(r'class')

                # Extract function body
                if is_class:
                    body = self._extract_class_body(code, match.start())
                else:
                    body = self._extract_function_body(code, match.start())

                tests.append({
                    "name": name,
                    "line": line_num,
                    "is_class": is_class,
                    "body": body,
                    "body_lines": body.count('\n') if body else 0
                })

        return tests

    def _find_all_functions(self, code: str) -> List[str]:
        """Find all function definitions."""
        return [m.group(1) for m in re.finditer(r'(?:async\s+)?def\s+(\w+)', code)]

    def _analyze_test_quality(self, test_functions: List[Dict], code: str) -> Dict:
        """Analyze the quality of test functions."""
        findings = []
        quality_metrics = {
            "short_tests": 0,
            "long_tests": 0,
            "empty_tests": 0,
            "assertion_less_tests": 0
        }

        for test in test_functions:
            if test["is_class"]:
                continue

            body = test["body"]
            body_lines = body.strip().split('\n') if body else []

            # Check for empty tests
            if not body or len(body.strip().split('\n')) <= 1:
                quality_metrics["empty_tests"] += 1
                findings.append({
                    "severity": "warning",
                    "category": "empty_test",
                    "message": f"Test '{test['name']}' appears to be empty or has no body",
                    "line_start": test["line"],
                    "suggestion": "Add test implementation or remove the placeholder test",
                    "confidence": 0.9
                })
                continue

            # Check for assertions
            has_assertion = any(
                re.search(pattern, body) for pattern in self.ASSERTION_PATTERNS
            )
            if not has_assertion:
                quality_metrics["assertion_less_tests"] += 1
                findings.append({
                    "severity": "warning",
                    "category": "no_assertion",
                    "message": f"Test '{test['name']}' has no assertions",
                    "line_start": test["line"],
                    "suggestion": "Add assertions to verify expected behavior",
                    "confidence": 0.85
                })

            # Check test length
            if test["body_lines"] > 30:
                quality_metrics["long_tests"] += 1
                findings.append({
                    "severity": "info",
                    "category": "long_test",
                    "message": f"Test '{test['name']}' is {test['body_lines']} lines long",
                    "line_start": test["line"],
                    "suggestion": "Consider breaking long tests into focused test cases",
                    "confidence": 0.7
                })

        summary = {
            "total_tests": len(test_functions),
            "empty_tests": quality_metrics["empty_tests"],
            "assertion_less_tests": quality_metrics["assertion_less_tests"],
            "long_tests": quality_metrics["long_tests"],
            "quality_ratio": round(
                (len(test_functions) - quality_metrics["empty_tests"] - quality_metrics["assertion_less_tests"])
                / max(1, len(test_functions)) * 100, 1
            )
        }

        return {"findings": findings, "summary": summary}

    def _analyze_assertions(self, code: str, test_functions: List[Dict]) -> Dict:
        """Analyze assertion usage in tests."""
        findings = []
        assertion_types = defaultdict(int)

        for pattern in self.ASSERTION_PATTERNS:
            matches = re.findall(pattern, code)
            if matches:
                assertion_types[pattern.split('(')[0].split('\\')[0].strip('b')] = len(matches)

        total_assertions = sum(assertion_types.values())

        # Check for assert True/False instead of specific assertions
        basic_asserts = len(re.findall(r'\bassert\s+(True|False)\b', code))
        if basic_asserts > total_assertions * 0.5 and basic_asserts > 3:
            findings.append({
                "severity": "info",
                "category": "assertion_quality",
                "message": f"Using basic assert True/False ({basic_asserts} times) instead of specific assertions",
                "suggestion": "Use specific assertions (assertEqual, assertIn, etc.) for better error messages",
                "confidence": 0.8
            })

        return {
            "findings": findings,
            "total_assertions": total_assertions,
            "assertion_types": dict(assertion_types)
        }

    def _check_test_isolation(self, code: str, test_functions: List[Dict]) -> List[Dict]:
        """Check for proper test isolation."""
        findings = []

        # Check for global state modification
        global_mods = re.findall(r'^(\s*)(global\s+\w+)', code, re.MULTILINE)
        if global_mods:
            findings.append({
                "severity": "warning",
                "category": "test_isolation",
                "message": f"Found {len(global_mods)} global variable modifications in tests",
                "suggestion": "Avoid modifying global state in tests; use fixtures or mocks",
                "confidence": 0.85
            })

        # Check for hardcoded file paths
        file_paths = re.findall(r'open\s*\(\s*[\'"][/\\]', code)
        if file_paths:
            findings.append({
                "severity": "warning",
                "category": "test_isolation",
                "message": f"Found {len(file_paths)} hardcoded file paths",
                "suggestion": "Use temporary directories or mock file operations",
                "confidence": 0.8
            })

        # Check for sleep/time-dependent tests
        time_deps = re.findall(r'\b(time\.sleep|datetime\.now|time\.time)\b', code)
        if time_deps:
            findings.append({
                "severity": "info",
                "category": "test_isolation",
                "message": f"Found {len(time_deps)} time-dependent operations",
                "suggestion": "Mock time-dependent operations for deterministic tests",
                "confidence": 0.7
            })

        return findings

    def _check_edge_cases(self, code: str, test_functions: List[Dict]) -> List[Dict]:
        """Check for edge case coverage."""
        findings = []

        edge_case_patterns = {
            "null_none": r'\b(None|null|NULL)\b',
            "empty_collections": r'\b(\[\]|\{\}|""|\'\'|\(\))',
            "boundary_values": r'\b(0|1|-1|MAX|MIN|sys\.maxsize|float\(\'inf\'|float\(\'-inf\')',
            "negative_numbers": r'(?<=[\s(,])-[\d]+',
            "large_values": r'\b\d{6,}\b',
            "special_strings": r'["\']([^"\']{0,2})["\']|["\'](\s+)["\']',
        }

        found_edge_cases = set()
        for case_type, pattern in edge_case_patterns.items():
            if re.search(pattern, code):
                found_edge_cases.add(case_type)

        if len(found_edge_cases) < 3 and test_functions:
            findings.append({
                "severity": "info",
                "category": "edge_cases",
                "message": f"Limited edge case coverage (found: {', '.join(found_edge_cases) or 'none'})",
                "suggestion": "Add tests for None, empty collections, boundary values, and negative cases",
                "confidence": 0.7
            })

        return findings

    def _check_mock_usage(self, code: str, test_functions: List[Dict]) -> List[Dict]:
        """Check mock/patch usage in tests."""
        findings = []

        mock_patterns = [
            r'\bmock\b',
            r'\bpatch\b',
            r'\bMagicMock\b',
            r'\bMock\(\)',
            r'\bmonkeypatch\b',
        ]

        mock_count = sum(len(re.findall(p, code, re.IGNORECASE)) for p in mock_patterns)

        # Check for external dependencies without mocking
        external_deps = re.findall(r'(requests\.\w+|urllib\.\w+|http\.\w+)', code)
        if external_deps and mock_count == 0:
            findings.append({
                "severity": "warning",
                "category": "mock_usage",
                "message": f"External HTTP calls found without mocking ({len(external_deps)} calls)",
                "suggestion": "Mock external HTTP calls to avoid network dependencies in tests",
                "confidence": 0.85
            })

        return findings

    def _check_test_documentation(self, test_functions: List[Dict], code: str) -> List[Dict]:
        """Check test documentation and description."""
        findings = []

        for test in test_functions:
            if test["is_class"]:
                continue

            # Check for docstring
            body = test["body"]
            if body:
                stripped_body = body.strip()
                # Find the docstring after def line
                after_def = re.sub(r'^.*?:\s*\n', '', stripped_body, count=1, flags=re.DOTALL)
                has_docstring = after_def.lstrip().startswith(('"""', "'''"))

                if not has_docstring and test["body_lines"] > 5:
                    # Long tests should have descriptions
                    findings.append({
                        "severity": "info",
                        "category": "test_documentation",
                        "message": f"Test '{test['name']}' has no description",
                        "line_start": test["line"],
                        "suggestion": "Add a docstring explaining what this test verifies",
                        "confidence": 0.6
                    })

        return findings[:5]

    def _check_test_naming(self, test_functions: List[Dict]) -> List[Dict]:
        """Check test function naming quality."""
        findings = []

        for test in test_functions:
            if test["is_class"]:
                continue

            name = test["name"]
            # Remove prefix
            clean_name = re.sub(r'^(test_|it_|should_)', '', name)

            # Check if name describes behavior
            if len(clean_name) < 5:
                findings.append({
                    "severity": "info",
                    "category": "test_naming",
                    "message": f"Test name '{name}' is too short to describe behavior",
                    "line_start": test["line"],
                    "suggestion": "Use descriptive names like 'test_user_login_with_invalid_password'",
                    "confidence": 0.7
                })
            elif '_' not in clean_name and len(clean_name) > 15:
                findings.append({
                    "severity": "info",
                    "category": "test_naming",
                    "message": f"Test name '{name}' could be more readable with underscores",
                    "line_start": test["line"],
                    "confidence": 0.6
                })

        return findings[:5]

    def _extract_class_body(self, code: str, start: int) -> str:
        """Extract class body."""
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
        """Extract function body."""
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

    def _calculate_score(self, test_ratio: float, assertion_density: float,
                        finding_count: int, test_quality: Dict) -> float:
        """Calculate test coverage score (0-100)."""
        # Test ratio component (30%)
        ratio_score = min(100, test_ratio * 2)

        # Assertion density component (25%)
        # Good tests have 2-5 assertions per test
        if assertion_density < 1:
            density_score = 30
        elif assertion_density < 2:
            density_score = 60
        elif assertion_density <= 5:
            density_score = 90
        else:
            density_score = 75  # Too many assertions might indicate testing too much

        # Quality component (25%)
        quality_score = test_quality["summary"].get("quality_ratio", 50)

        # Finding penalty (20%)
        finding_penalty = max(0, 100 - finding_count * 5)

        score = (
            ratio_score * 0.30 +
            density_score * 0.25 +
            quality_score * 0.25 +
            finding_penalty * 0.20
        )

        return max(0, min(100, round(score, 1)))
