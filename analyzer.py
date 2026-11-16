"""
analyzer.py - static analysis: reads the code WITHOUT running it.

It produces
  1. complexity  : Big-O guess from loop nesting (plus hidden loops like sum() or comprehensions)
  2. findings    : a list of inefficient patterns, each with a plain-English explanation
  3. score       : a 0-100 GreenTrace score (100 = nothing found, simple complexity)

The score is a simple heuristic you can explain in your report:
    score = 100 - complexity penalty - findings penalty (findings penalty is capped at 40)
"""
import ast

COMPLEXITY_PENALTY = {0: 0, 1: 5, 2: 25, 3: 45}          # 4 or more nested loops: 60
FINDING_PENALTY = {"high": 15, "medium": 8, "low": 3}
SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}

HIDDEN_LOOP_CALLS = {"sum", "min", "max", "any", "all", "sorted", "map", "filter"}


def loop_depth(node, depth=0):
    """Deepest level of nested for/while loops."""
    deepest = depth
    for child in ast.iter_child_nodes(node):
        here = loop_depth(child, depth + 1 if isinstance(child, (ast.For, ast.While)) else depth)
        deepest = max(deepest, here)
    return deepest


def complexity_of(tree):
    depth = loop_depth(tree)
    loops = sum(isinstance(n, (ast.For, ast.While)) for n in ast.walk(tree))

    # Comprehensions and builtins like sum() loop internally: count them as one level.
    for n in ast.walk(tree):
        comprehension = isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
        loop_builtin = (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        and n.func.id in HIDDEN_LOOP_CALLS)
        if comprehension or loop_builtin:
            depth = max(depth, 1)

    makes_container = any(isinstance(n, (ast.List, ast.Dict, ast.Set, ast.ListComp,
                                         ast.DictComp, ast.SetComp)) for n in ast.walk(tree))
    time = {0: "O(1)", 1: "O(n)", 2: "O(n\u00B2)", 3: "O(n\u00B3)"}.get(depth, f"O(n^{depth})")
    grade = {0: "A+", 1: "A", 2: "C", 3: "D"}.get(depth, "F")
    space = "O(n)" if (makes_container and depth >= 1) else "O(1)"
    return {"time": time, "space": space, "depth": depth, "loops": loops, "grade": grade}


def finding(rule_id, title, severity, line, message, why, auto_fix=False):
    return {"rule_id": rule_id, "title": title, "severity": severity, "line": line,
            "message": message, "why": why, "auto_fix": auto_fix}


def generic_findings(tree, depth, covered):
    """Patterns we can point out even when the optimizer has no automatic fix."""
    found = []
    loops = [n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))]

    # 1) nested loops
    if depth >= 2 and "pair_search" not in covered:
        outer = next(n for n in loops)       # first loop in the file
        found.append(finding(
            "nested_loops", "Nested loops", "high" if depth >= 3 else "medium", outer.lineno,
            f"Loops are nested {depth} levels deep, so the work grows roughly like n^{depth}.",
            "Each extra level of nesting multiplies the number of steps the CPU performs. "
            "Using a set or dictionary for lookups often removes one level."))

    # 2) `x in some_list` inside a loop
    list_names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = n.value
            is_list = isinstance(v, (ast.List, ast.ListComp)) or (
                isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "list")
            if is_list:
                list_names.add(n.targets[0].id)
    seen_lines = set()
    for loop in loops:
        for n in ast.walk(loop):
            if (isinstance(n, ast.Compare) and any(isinstance(op, (ast.In, ast.NotIn)) for op in n.ops)
                    and isinstance(n.comparators[0], ast.Name) and n.comparators[0].id in list_names
                    and n.lineno not in seen_lines):
                seen_lines.add(n.lineno)
                found.append(finding(
                    "list_membership", "Membership test on a list inside a loop", "medium", n.lineno,
                    f"'{n.comparators[0].id}' is a list, and searching a list is O(n) every time.",
                    "A set finds an item in constant time, so converting the list to a set before "
                    "the loop turns n searches of n items into n quick lookups."))

    # 3) building a string with += inside a loop
    seen_lines = set()
    for loop in loops:
        for n in ast.walk(loop):
            if (isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Add)
                    and isinstance(n.value, (ast.JoinedStr, ast.Constant))
                    and (isinstance(n.value, ast.JoinedStr) or isinstance(n.value.value, str))
                    and n.lineno not in seen_lines):
                seen_lines.add(n.lineno)
                found.append(finding(
                    "string_concat", "String built with += inside a loop", "low", n.lineno,
                    "Each += creates a brand-new string and copies the old one.",
                    "Collecting the pieces in a list and calling ''.join(pieces) once copies the text only once."))
    return found


def analyze(code, opportunities=None):
    """
    opportunities = the list returned by optimizer.optimize() for this code
    (rewrites that COULD be applied). They are shown as findings too.
    """
    tree = ast.parse(code)
    complexity = complexity_of(tree)
    opportunities = opportunities or []

    findings = [finding(o["rule_id"], o["title"], o["severity"], o["line"],
                        f"Line {o['line']}: expected gain \u2013 {o['gain']}.", o["why"], auto_fix=True)
                for o in opportunities]
    findings += generic_findings(tree, complexity["depth"], {o["rule_id"] for o in opportunities})
    findings.sort(key=lambda f: (-SEVERITY_ORDER[f["severity"]], f["line"]))

    complexity_penalty = COMPLEXITY_PENALTY.get(complexity["depth"], 60)
    findings_penalty = min(40, sum(FINDING_PENALTY[f["severity"]] for f in findings))
    score = max(0, 100 - complexity_penalty - findings_penalty)

    return {"complexity": complexity, "findings": findings, "score": score}
