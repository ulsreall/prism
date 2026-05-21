"""
PRISM - Coupling Analyzer Agent
Estimated token consumption: ~18K tokens per analysis

Analyzes:
- Afferent Coupling (Ca) - incoming dependencies
- Efferent Coupling (Ce) - outgoing dependencies
- Instability (I = Ce / (Ca + Ce))
- Abstractness (A)
- Distance from Main Sequence (D = |A + I - 1|)
- Package dependency cycles
- Module cohesion
"""

import re
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict


class CouplingAnalyzerAgent:
    """Agent for analyzing code coupling and dependency metrics."""

    AGENT_NAME = "Coupling Analyzer"
    ESTIMATED_TOKENS = 18000

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Analyze coupling metrics across multiple dimensions."""
        findings = []
        lines = code.split('\n')

        # 1. Import dependency analysis
        import_deps = self._analyze_import_dependencies(code)

        # 2. Class coupling analysis
        class_coupling = self._analyze_class_coupling(code)

        # 3. Function coupling analysis
        func_coupling = self._analyze_function_coupling(code)

        # 4. Cohesion analysis
        cohesion = self._analyze_cohesion(code)

        # 5. Dependency direction analysis
        dep_direction = self._analyze_dependency_direction(code)

        # 6. Circular dependency detection
        circular_findings = self._detect_circular_dependencies(code)
        findings.extend(circular_findings)

        # 7. Feature envy (class-level)
        envy_findings = self._detect_class_feature_envy(code)
        findings.extend(envy_findings)

        # 8. Middle man detection
        middle_man_findings = self._detect_middle_man(code)
        findings.extend(middle_man_findings)

        # Calculate coupling metrics
        ca = import_deps["afferent"]  # Incoming dependencies
        ce = import_deps["efferent"]  # Outgoing dependencies

        # Instability: I = Ce / (Ca + Ce), range [0,1]
        instability = ce / max(1, ca + ce)

        # Abstractness (ratio of abstract classes/methods)
        abstractness = self._calculate_abstractness(code)

        # Distance from main sequence: D = |A + I - 1|
        distance = abs(abstractness + instability - 1)

        # Generate findings based on metrics
        if ce > 15:
            findings.append({
                "severity": "error",
                "category": "high_coupling",
                "message": f"High efferent coupling: {ce} outgoing dependencies",
                "suggestion": "Reduce dependencies by using dependency injection or interface segregation",
                "confidence": 0.9
            })
        elif ce > 10:
            findings.append({
                "severity": "warning",
                "category": "high_coupling",
                "message": f"Moderate efferent coupling: {ce} outgoing dependencies",
                "suggestion": "Consider reducing the number of imports",
                "confidence": 0.8
            })

        if instability > 0.8:
            findings.append({
                "severity": "warning",
                "category": "instability",
                "message": f"High instability: {instability:.2f} (should be balanced with abstractness)",
                "suggestion": "This module is very dependent on others. Consider adding abstractions.",
                "confidence": 0.8
            })

        if distance > 0.5:
            findings.append({
                "severity": "info",
                "category": "design_balance",
                "message": f"Distance from main sequence: {distance:.2f} (ideal is close to 0)",
                "suggestion": "Balance abstractness and stability according to the main sequence principle",
                "confidence": 0.7
            })

        # Calculate overall score
        score = self._calculate_score(
            ca, ce, instability, abstractness, distance, cohesion, len(findings)
        )

        metrics = {
            "score": score,
            "coupling": {
                "afferent": ca,
                "efferent": ce,
                "total": ca + ce
            },
            "instability": round(instability, 3),
            "abstractness": round(abstractness, 3),
            "distance_from_main_sequence": round(distance, 3),
            "cohesion": cohesion,
            "import_analysis": import_deps,
            "class_coupling": class_coupling,
            "function_coupling": func_coupling,
            "dependency_direction": dep_direction
        }

        tokens_used = len(code) // 3 + len(findings) * 180 + 600
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _analyze_import_dependencies(self, code: str) -> Dict:
        """Analyze import-based dependencies."""
        imports = {
            "standard_library": [],
            "third_party": [],
            "local": [],
            "total": 0
        }

        efferent = 0  # Outgoing dependencies
        import_modules = set()

        for match in re.finditer(r'^(?:from\s+(\S+)|import\s+(\S+))', code, re.MULTILINE):
            module = match.group(1) or match.group(2)
            if module:
                module_base = module.split('.')[0]
                import_modules.add(module_base)
                efferent += 1

                # Categorize
                stdlib_modules = {
                    'os', 'sys', 're', 'json', 'math', 'datetime', 'time',
                    'typing', 'collections', 'abc', 'io', 'pathlib', 'logging',
                    'unittest', 'hashlib', 'copy', 'functools', 'itertools',
                    'asyncio', 'threading', 'multiprocessing', 'socket', 'http',
                    'urllib', 'email', 'html', 'xml', 'csv', 'sqlite3',
                    'contextlib', 'dataclasses', 'enum', 'struct', 'array',
                    'queue', 'heapq', 'bisect', 'weakref', 'types', 'operator',
                    'string', 'textwrap', 'difflib', 'pprint', 'traceback'
                }
                if module_base in stdlib_modules:
                    imports["standard_library"].append(module)
                elif module_base in ('.', '..'):
                    imports["local"].append(module)
                else:
                    imports["third_party"].append(module)

        imports["total"] = efferent

        return {
            "efferent": efferent,
            "afferent": 0,  # Can't determine from single file
            "modules": list(import_modules),
            "categories": imports,
            "unique_modules": len(import_modules)
        }

    def _analyze_class_coupling(self, code: str) -> Dict:
        """Analyze coupling between classes."""
        classes = list(re.finditer(r'class\s+(\w+)(?:\(([^)]*)\))?\s*:', code))

        class_deps = {}
        for cls_match in classes:
            cls_name = cls_match.group(1)
            base_classes = cls_match.group(2) or ""
            cls_body = self._extract_class_body(code, cls_match.start())

            # Count references to other classes
            other_class_refs = 0
            for other_cls in classes:
                other_name = other_cls.group(1)
                if other_name != cls_name:
                    ref_count = len(re.findall(rf'\b{other_name}\b', cls_body))
                    other_class_refs += ref_count

            # Count method parameters with class types
            param_types = re.findall(r':\s*(\w+)', cls_body)
            type_refs = sum(1 for t in param_types if t[0].isupper())

            class_deps[cls_name] = {
                "base_classes": [b.strip() for b in base_classes.split(',') if b.strip()],
                "external_class_refs": other_class_refs,
                "type_references": type_refs,
                "method_count": len(re.findall(r'def\s+\w+', cls_body)),
                "lines": cls_body.count('\n')
            }

        return {
            "class_count": len(classes),
            "class_dependencies": class_deps,
            "avg_coupling": round(
                sum(d["external_class_refs"] for d in class_deps.values()) /
                max(1, len(class_deps)), 2
            )
        }

    def _analyze_function_coupling(self, code: str) -> Dict:
        """Analyze coupling between functions."""
        functions = list(re.finditer(r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)', code))

        func_deps = {}
        for func_match in functions:
            func_name = func_match.group(1)
            func_body = self._extract_function_body(code, func_match.start())

            # Count calls to other functions
            calls_to_others = 0
            for other_func in functions:
                other_name = other_func.group(1)
                if other_name != func_name:
                    calls_to_others += len(re.findall(rf'\b{other_name}\s*\(', func_body))

            # Count parameter count
            params = func_match.group(2)
            param_count = len([p.strip() for p in params.split(',')
                             if p.strip() and p.strip() != 'self'])

            func_deps[func_name] = {
                "calls_to_others": calls_to_others,
                "parameter_count": param_count,
                "body_length": func_body.count('\n') if func_body else 0
            }

        return {
            "function_count": len(functions),
            "avg_calls_to_others": round(
                sum(d["calls_to_others"] for d in func_deps.values()) /
                max(1, len(func_deps)), 2
            ),
            "avg_parameter_count": round(
                sum(d["parameter_count"] for d in func_deps.values()) /
                max(1, len(func_deps)), 2
            ),
            "high_coupling_functions": [
                name for name, deps in func_deps.items()
                if deps["calls_to_others"] > 5
            ]
        }

    def _analyze_cohesion(self, code: str) -> Dict:
        """Analyze module/class cohesion."""
        classes = list(re.finditer(r'class\s+(\w+)', code))

        cohesion_scores = []
        for cls_match in classes:
            cls_name = cls_match.group(1)
            cls_body = self._extract_class_body(code, cls_match.start())

            # Get methods and instance variables
            methods = re.findall(r'def\s+(\w+)', cls_body)
            instance_vars = set(re.findall(r'self\.(\w+)', cls_body))

            if not methods or not instance_vars:
                cohesion_scores.append(1.0)
                continue

            # Calculate LCOM (Lack of Cohesion in Methods)
            # Count methods that use each instance variable
            var_method_usage = {}
            for var in instance_vars:
                using_methods = sum(
                    1 for method in methods
                    if re.search(rf'self\.{var}\b',
                                cls_body[cls_body.find(f'def {method}'):
                                        cls_body.find(f'def {methods[methods.index(method)+1]}')
                                        if methods.index(method) < len(methods)-1
                                        else len(cls_body)])
                )
                var_method_usage[var] = using_methods

            # Simple cohesion: ratio of methods using shared state
            if var_method_usage:
                avg_usage = sum(var_method_usage.values()) / len(var_method_usage)
                cohesion = min(1.0, avg_usage / max(1, len(methods)))
            else:
                cohesion = 0.5

            cohesion_scores.append(cohesion)

        return {
            "module_cohesion": round(
                sum(cohesion_scores) / max(1, len(cohesion_scores)), 3
            ) if cohesion_scores else 1.0,
            "class_count": len(cohesion_scores),
            "low_cohesion_classes": sum(1 for s in cohesion_scores if s < 0.3)
        }

    def _analyze_dependency_direction(self, code: str) -> Dict:
        """Analyze dependency direction (should flow inward)."""
        imports = re.findall(r'from\s+(\S+)\s+import', code)

        # Categorize by layer
        layers = {
            "presentation": 0,
            "business": 0,
            "data": 0,
            "infrastructure": 0,
            "unknown": 0
        }

        for imp in imports:
            imp_lower = imp.lower()
            if any(kw in imp_lower for kw in ['view', 'template', 'ui', 'web', 'api', 'route']):
                layers["presentation"] += 1
            elif any(kw in imp_lower for kw in ['model', 'service', 'domain', 'entity', 'logic']):
                layers["business"] += 1
            elif any(kw in imp_lower for kw in ['db', 'database', 'repository', 'dao', 'storage']):
                layers["data"] += 1
            elif any(kw in imp_lower for kw in ['util', 'helper', 'config', 'infra', 'common']):
                layers["infrastructure"] += 1
            else:
                layers["unknown"] += 1

        return {
            "layer_dependencies": layers,
            "total_dependencies": sum(layers.values()),
            "architecture_hint": self._infer_architecture(layers)
        }

    def _detect_circular_dependencies(self, code: str) -> List[Dict]:
        """Detect potential circular dependency patterns."""
        findings = []

        # Check for mutual imports (simplified)
        imports = re.findall(r'from\s+(\w+)', code)
        import_counts = defaultdict(int)
        for imp in imports:
            import_counts[imp] += 1

        for module, count in import_counts.items():
            if count > 1:
                findings.append({
                    "severity": "info",
                    "category": "duplicate_import",
                    "message": f"Module '{module}' imported {count} times",
                    "suggestion": "Consolidate imports from the same module",
                    "confidence": 0.9
                })

        return findings

    def _detect_class_feature_envy(self, code: str) -> List[Dict]:
        """Detect classes that use more external data than their own."""
        findings = []
        classes = list(re.finditer(r'class\s+(\w+)', code))

        for cls_match in classes:
            cls_name = cls_match.group(1)
            cls_body = self._extract_class_body(code, cls_match.start())

            self_refs = len(re.findall(r'self\.\w+', cls_body))
            # Count references to other classes' methods/attributes
            other_refs = 0
            for other_cls in classes:
                other_name = other_cls.group(1)
                if other_name != cls_name:
                    other_refs += len(re.findall(rf'\w+\.{other_name}', cls_body))

            if other_refs > self_refs * 2 and self_refs > 0:
                findings.append({
                    "severity": "warning",
                    "category": "feature_envy",
                    "message": f"Class '{cls_name}' may belong elsewhere (uses {other_refs} external vs {self_refs} self refs)",
                    "suggestion": f"Consider moving '{cls_name}' closer to the data it uses",
                    "confidence": 0.75
                })

        return findings

    def _detect_middle_man(self, code: str) -> List[Dict]:
        """Detect classes that mostly delegate to other classes."""
        findings = []
        classes = list(re.finditer(r'class\s+(\w+)', code))

        for cls_match in classes:
            cls_name = cls_match.group(1)
            cls_body = self._extract_class_body(code, cls_match.start())

            methods = re.findall(r'def\s+(\w+)\s*\(self[^)]*\)(.*?)(?=\n\s*def|\Z)',
                               cls_body, re.DOTALL)

            delegation_count = 0
            for method_name, method_body in methods:
                # Check if method just calls another object's method
                stripped_body = method_body.strip()
                lines = [l.strip() for l in stripped_body.split('\n') if l.strip() and not l.strip().startswith('#')]

                if len(lines) <= 2:
                    # Very short method body
                    for line in lines:
                        if re.search(r'return\s+\w+\.\w+\(', line):
                            delegation_count += 1

            if delegation_count > 3 and len(methods) > 0:
                delegation_ratio = delegation_count / len(methods)
                if delegation_ratio > 0.5:
                    findings.append({
                        "severity": "info",
                        "category": "middle_man",
                        "message": f"Class '{cls_name}' is mostly delegating ({delegation_count}/{len(methods)} methods)",
                        "suggestion": "Consider if this class adds enough value or if callers should use the delegate directly",
                        "confidence": 0.7
                    })

        return findings

    def _calculate_abstractness(self, code: str) -> float:
        """Calculate abstractness ratio."""
        # Count abstract classes and methods
        abstract_classes = len(re.findall(r'class\s+\w+\s*\(\s*ABC\s*\)', code))
        abstract_methods = len(re.findall(r'@abstractmethod', code))

        total_classes = len(re.findall(r'class\s+\w+', code))
        total_methods = len(re.findall(r'def\s+\w+', code))

        if total_classes == 0 and total_methods == 0:
            return 0.0

        class_abstractness = abstract_classes / max(1, total_classes)
        method_abstractness = abstract_methods / max(1, total_methods)

        return (class_abstractness + method_abstractness) / 2

    def _infer_architecture(self, layers: Dict) -> str:
        """Infer architecture pattern from layer dependencies."""
        total = sum(layers.values())
        if total == 0:
            return "unknown"

        if layers["presentation"] > total * 0.5:
            return "mvc_like"
        elif layers["data"] > total * 0.4:
            return "data_driven"
        elif layers["business"] > total * 0.4:
            return "domain_driven"
        else:
            return "layered"

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

    def _calculate_score(self, ca: int, ce: int, instability: float,
                        abstractness: float, distance: float,
                        cohesion: Dict, finding_count: int) -> float:
        """Calculate coupling score (0-100, higher is better)."""
        score = 100.0

        # Penalize high efferent coupling
        if ce > 15:
            score -= 25
        elif ce > 10:
            score -= 15
        elif ce > 7:
            score -= 5

        # Penalize extreme instability
        if instability > 0.9:
            score -= 15
        elif instability > 0.7:
            score -= 5

        # Penalize high distance from main sequence
        if distance > 0.5:
            score -= 15
        elif distance > 0.3:
            score -= 5

        # Penalize low cohesion
        module_cohesion = cohesion.get("module_cohesion", 1.0)
        if module_cohesion < 0.3:
            score -= 15
        elif module_cohesion < 0.5:
            score -= 5

        # Penalize findings
        score -= min(20, finding_count * 2)

        return max(0, min(100, round(score, 1)))
