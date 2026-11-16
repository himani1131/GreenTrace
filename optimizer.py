"""
optimizer.py - rewrites slow-but-common Python patterns into faster ones.

It reads the code as a syntax tree (the `ast` module), so it understands the
structure of the code instead of guessing with text search.

Every rule looks at one statement (or two in a row) and returns a replacement,
or None when the pattern does not match. Rules are deliberately conservative:
when unsure, they do nothing. app.py also RUNS the rewritten code on test cases
and throws the rewrite away if the output changes.
"""
import ast

# Information shown to the user for each rule (also stored in the SQLite `rules` table).
RULES = {
    "pair_search": {
        "title": "Nested pair search replaced by a position index",
        "severity": "high",
        "gain": "O(n\u00B2) \u2192 O(n)",
        "why": "Checking every pair of items takes n \u00D7 n steps. Remembering where each "
               "value occurs lets the program look the partner up directly instead of searching for it.",
    },
    "licm": {
        "title": "Loop-invariant computation moved out of the loop",
        "severity": "medium",
        "gain": "less work per iteration",
        "why": "The same calculation was repeated in every iteration even though its inputs never "
               "change inside the loop. Calculating it once before the loop removes that repeated CPU work.",
    },
    "append_loop": {
        "title": "Append loop replaced by a list comprehension",
        "severity": "low",
        "gain": "less interpreter overhead",
        "why": "A list comprehension builds the list in one optimized step instead of calling "
               "append() once per item.",
    },
    "sum_loop": {
        "title": "Manual sum loop replaced by sum()",
        "severity": "low",
        "gain": "less interpreter overhead",
        "why": "The built-in sum() runs in Python's fast C code, so it avoids the cost of an explicit loop.",
    },
}

# Function calls that cannot change variables behind our back.
PURE_CALLS = {"len", "abs", "min", "max", "round", "int", "float", "str", "bool", "sum", "sorted",
              "range", "enumerate", "zip", "list", "set", "dict", "tuple", "print", "isinstance",
              "ord", "chr", "divmod", "pow", "reversed", "any", "all", "map", "filter"}

# Calls that are allowed INSIDE an expression we move out of a loop.
SAFE_EXPR_CALLS = {"len", "abs", "min", "max", "round", "int", "float"}


class State:
    """Counter used to give unique names (_inv1, _inv2, ...) to hoisted values."""
    temp_count = 0


# ------------------------------------------------------------------ helpers
def names_in(node):
    """Every variable name used inside a piece of code."""
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def names_in_all(statements):
    names = set()
    for stmt in statements:
        names |= names_in(stmt)
    return names


def value_names(node):
    """Like names_in, but ignores the names of functions being called (len, abs...)."""
    called = {n.func.id for n in ast.walk(node)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    return names_in(node) - called


def root_name(node):
    """For a.b[c].d return 'a'."""
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def range_len_of(node):
    """If node is range(len(X)) return X as text, otherwise None."""
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "range" and len(node.args) == 1):
        arg = node.args[0]
        if (isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name)
                and arg.func.id == "len" and len(arg.args) == 1):
            return ast.unparse(arg.args[0])
    return None


def append_call(stmt):
    """If stmt is  name.append(x)  return (name, x), otherwise None."""
    if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and stmt.value.func.attr == "append"
            and isinstance(stmt.value.func.value, ast.Name)
            and len(stmt.value.args) == 1 and not stmt.value.keywords):
        return stmt.value.func.value.id, stmt.value.args[0]
    return None


# ------------------------------------------------------------------ rule 1
def rule_pair_search(stmt):
    """
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if a[i] + a[j] == t:
                out.append((a[i], a[j]))
    -> build a dictionary of positions once, then look each partner up.
    Same pairs in the same order, O(n^2) -> O(n).
    """
    if not (isinstance(stmt, ast.For) and not stmt.orelse and isinstance(stmt.target, ast.Name)):
        return None
    i = stmt.target.id
    a = range_len_of(stmt.iter)
    if a is None or len(stmt.body) != 1 or not isinstance(stmt.body[0], ast.For):
        return None

    inner = stmt.body[0]
    if inner.orelse or not isinstance(inner.target, ast.Name):
        return None
    j = inner.target.id
    if ast.unparse(inner.iter) != f"range({i} + 1, len({a}))":
        return None
    if len(inner.body) != 1 or not isinstance(inner.body[0], ast.If):
        return None

    check = inner.body[0]
    if check.orelse or len(check.body) != 1:
        return None
    test = check.test
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
        return None
    if ast.unparse(test.left) != f"{a}[{i}] + {a}[{j}]":
        return None
    target = test.comparators[0]
    if names_in(target) & {i, j}:
        return None

    found = append_call(check.body[0])
    if found is None or ast.unparse(found[1]) != f"({a}[{i}], {a}[{j}])":
        return None
    out = found[0]

    new_code = f"""
_positions = {{}}
for _k, _v in enumerate({a}):
    _positions.setdefault(_v, []).append(_k)
for {i} in range(len({a})):
    _later = _positions.get({ast.unparse(target)} - {a}[{i}], [])
    {out}.extend(({a}[{i}], {a}[_j]) for _j in _later[bisect_right(_later, {i}):])
"""
    return ast.parse(new_code).body


# ------------------------------------------------------------------ rule 2
def rule_sum_loop(stmt, nxt, rest):
    """
    total = 0
    for x in items:
        total += x
    -> total = sum(items)
    """
    if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and isinstance(stmt.value, ast.Constant) and type(stmt.value.value) is int
            and stmt.value.value == 0):
        return None
    if not (isinstance(nxt, ast.For) and not nxt.orelse
            and isinstance(nxt.target, ast.Name) and len(nxt.body) == 1):
        return None

    total = stmt.targets[0].id
    item = nxt.target.id
    step = nxt.body[0]
    if not (isinstance(step, ast.AugAssign) and isinstance(step.op, ast.Add)
            and isinstance(step.target, ast.Name) and step.target.id == total
            and isinstance(step.value, ast.Name) and step.value.id == item):
        return None
    if total == item or total in names_in(nxt.iter):
        return None
    if item in names_in_all(rest):          # the loop variable is used later -> keep the loop
        return None
    return ast.parse(f"{total} = sum({ast.unparse(nxt.iter)})").body[0]


# ------------------------------------------------------------------ rule 3
def rule_append_loop(stmt, nxt, rest):
    """
    out = []
    for x in items:
        [tmp = f(x)]            (optional)
        [if cond:]              (optional)
            out.append(f(x))
    -> out = [f(x) for x in items [if cond]]
    """
    if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and isinstance(stmt.value, ast.List) and not stmt.value.elts):
        return None
    if not (isinstance(nxt, ast.For) and not nxt.orelse):
        return None

    out = stmt.targets[0].id
    body = nxt.body
    condition = None
    leaked = {n.id for n in ast.walk(nxt.target) if isinstance(n, ast.Name)}   # names that would disappear

    if len(body) == 1:
        inner = body[0]
        if isinstance(inner, ast.If) and not inner.orelse and len(inner.body) == 1:
            condition = inner.test
            inner = inner.body[0]
        found = append_call(inner)
        if found is None or found[0] != out:
            return None
        item = found[1]
    elif len(body) == 2:                                   # tmp = f(x) ; out.append(tmp)
        first, second = body
        if not (isinstance(first, ast.Assign) and len(first.targets) == 1
                and isinstance(first.targets[0], ast.Name)):
            return None
        tmp = first.targets[0].id
        found = append_call(second)
        if not (found and found[0] == out and isinstance(found[1], ast.Name) and found[1].id == tmp):
            return None
        if tmp in names_in(first.value) or tmp == out:
            return None
        item = first.value
        leaked.add(tmp)
    else:
        return None

    used = names_in(item) | names_in(nxt.iter)
    if condition is not None:
        used |= names_in(condition)
    if out in used:
        return None
    if leaked & names_in_all(rest):          # variables used after the loop -> keep the loop
        return None

    comprehension = ast.comprehension(
        target=nxt.target, iter=nxt.iter,
        ifs=[condition] if condition is not None else [], is_async=0)
    return ast.Assign(
        targets=[ast.Name(id=out, ctx=ast.Store())],
        value=ast.ListComp(elt=item, generators=[comprehension]),
        lineno=0)


# ------------------------------------------------------------------ rule 4 (loop-invariant code motion)
def is_safe(node):
    """
    True if evaluating the expression can never raise an error or change anything,
    so it is fine to evaluate it once BEFORE the loop (even if the loop runs 0 times).
    """
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float, str)) and not isinstance(node.value, bool)
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.UnaryOp):
        return isinstance(node.op, (ast.USub, ast.UAdd)) and is_safe(node.operand)
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            return is_safe(node.left) and is_safe(node.right)
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):      # only dividing by a non-zero constant
            right = node.right
            return (isinstance(right, ast.Constant) and isinstance(right.value, (int, float))
                    and not isinstance(right.value, bool) and right.value != 0 and is_safe(node.left))
        return False
    if isinstance(node, ast.Call):
        return (isinstance(node.func, ast.Name) and node.func.id in SAFE_EXPR_CALLS
                and not node.keywords and all(is_safe(a) for a in node.args))
    return False


def modified_names(loop):
    """Names whose value might change while the loop runs."""
    names = set()
    for n in ast.walk(loop):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            names.add(n.id)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            base = root_name(n.func.value)           # e.g. result.append(...) changes `result`
            if base:
                names.add(base)
        elif isinstance(n, (ast.Subscript, ast.Attribute)) and isinstance(n.ctx, ast.Store):
            base = root_name(n.value)                # e.g. data[i] = ... changes `data`
            if base:
                names.add(base)
    return names


def loop_is_simple(loop):
    """Skip loops that contain things we cannot reason about (own functions, globals, yield...)."""
    for n in ast.walk(loop):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef,
                          ast.Global, ast.Nonlocal, ast.Await, ast.Yield, ast.YieldFrom)):
            return False
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name) and n.func.id not in PURE_CALLS:
                return False
            if not isinstance(n.func, (ast.Name, ast.Attribute)):
                return False
    return True


class Hoister(ast.NodeTransformer):
    """
    Replaces calculations that do not depend on anything changing in the loop with
    a temporary variable (_inv1, ...). We only replace OPERANDS of bigger expressions,
    never a whole right-hand side, so a hoisted list or object can never be shared by accident.
    """

    def __init__(self, modified):
        self.modified = modified
        self.temps = {}          # expression text -> temp name
        self.assignments = []    # statements to place before the loop

    def invariant(self, node):
        if not isinstance(node, (ast.BinOp, ast.Call)):
            return False
        used = value_names(node)
        return bool(used) and not (used & self.modified) and is_safe(node)

    def operand(self, child):
        if self.invariant(child):
            key = ast.unparse(child)
            if key not in self.temps:
                State.temp_count += 1
                name = f"_inv{State.temp_count}"
                self.temps[key] = name
                self.assignments.append(ast.Assign(
                    targets=[ast.Name(id=name, ctx=ast.Store())], value=child, lineno=0))
            return ast.Name(id=self.temps[key], ctx=ast.Load())
        return self.visit(child)

    def visit_BinOp(self, node):
        node.left = self.operand(node.left)
        node.right = self.operand(node.right)
        return node

    def visit_UnaryOp(self, node):
        node.operand = self.operand(node.operand)
        return node

    def visit_Compare(self, node):
        node.left = self.operand(node.left)
        node.comparators = [self.operand(c) for c in node.comparators]
        return node

    def visit_BoolOp(self, node):
        node.values = [self.operand(v) for v in node.values]
        return node


def rule_licm(stmt):
    """
    for x in items:
        total += x * (a + b)        # (a + b) never changes
    -> _inv1 = a + b
       for x in items:
           total += x * _inv1
    """
    if not isinstance(stmt, (ast.For, ast.While)) or not loop_is_simple(stmt):
        return None
    hoister = Hoister(modified_names(stmt))
    for child in stmt.body:
        hoister.visit(child)
    if not hoister.assignments:
        return None
    return hoister.assignments + [stmt]


# ------------------------------------------------------------------ driver
def note(rule_id, line):
    info = RULES[rule_id]
    return {"rule_id": rule_id, "title": info["title"], "severity": info["severity"],
            "gain": info["gain"], "why": info["why"], "line": line}


def rewrite_block(statements, applied):
    """Walk a list of statements and replace the ones that match a rule."""
    result = []
    i = 0
    while i < len(statements):
        stmt = statements[i]
        nxt = statements[i + 1] if i + 1 < len(statements) else None
        rest = statements[i + 2:]

        new = rule_pair_search(stmt)
        if new:
            applied.append(note("pair_search", stmt.lineno))
            result.extend(new)
            i += 1
            continue

        new = rule_sum_loop(stmt, nxt, rest)
        if new:
            applied.append(note("sum_loop", nxt.lineno))
            result.append(new)
            i += 2
            continue

        new = rule_append_loop(stmt, nxt, rest)
        if new:
            applied.append(note("append_loop", nxt.lineno))
            result.append(new)
            i += 2
            continue

        new = rule_licm(stmt)
        if new:
            applied.append(note("licm", stmt.lineno))
            result.extend(new)
            i += 1
            continue

        result.append(stmt)
        i += 1
    return result


def walk(node, applied):
    for field in ("body", "orelse", "finalbody"):
        block = getattr(node, field, None)
        if isinstance(block, list):
            setattr(node, field, rewrite_block(block, applied))
    for child in ast.iter_child_nodes(node):
        walk(child, applied)


def optimize(code):
    """Returns (new_code, list_of_changes). If nothing matched, new_code is the original text."""
    State.temp_count = 0
    tree = ast.parse(code)
    applied = []
    walk(tree, applied)
    if not applied:
        return code, []

    new_code = ast.unparse(tree)
    if "bisect_right(" in new_code:
        new_code = "from bisect import bisect_right\n" + new_code
    return new_code, applied
