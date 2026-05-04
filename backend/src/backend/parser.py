from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Sense = Literal["<=", ">=", "<", ">", "="]

# Closed-form relaxation for strict inequalities (see modeling_notes in API).
STRICT_EPS: float = 1e-6
ObjSense = Literal["maximize", "minimize"]
VarDomain = Literal["continuous", "integer", "binary"]


class ParseError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "PARSE_ERROR",
        hint: str | None = None,
        context: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.hint = hint
        self.context = context or {}


@dataclass
class RawConstraint:
    coeffs: dict[str, float]
    rhs: float
    sense: Sense
    label: str


@dataclass
class ParsedLP:
    objective_sense: ObjSense
    objective: dict[str, float]
    constraints: list[RawConstraint] = field(default_factory=list)
    variable_domains: dict[str, VarDomain] = field(default_factory=dict)
    modeling_notes: list[str] = field(default_factory=list)

    @property
    def is_mip(self) -> bool:
        return any(domain in ("integer", "binary") for domain in self.variable_domains.values())


_TERM = re.compile(
    r"^([+-])(?:(\d+\.?\d*)\s*([a-z_][a-z0-9_]*)|(\d+\.?\d*)\s*$|([a-z_][a-z0-9_]*)\s*$)",
    re.IGNORECASE,
)


def _merge_coeff(dst: dict[str, float], var: str, c: float) -> None:
    if abs(c) < 1e-15:
        return
    dst[var] = dst.get(var, 0.0) + c


def parse_linear(expr: str) -> tuple[dict[str, float], float]:
    """Parse linear expression into (variable_coeffs, constant_term)."""
    t = expr.strip().lower()
    t = re.sub(r",\s*", " ", t)
    s = re.sub(r"\s+", "", t)
    if not s:
        raise ParseError("empty expression", code="EMPTY_EXPRESSION")
    if re.search(r"[\^*/]", s):
        raise ParseError(
            "only linear expressions are allowed (no *, /, powers)",
            code="NON_LINEAR_EXPRESSION",
            hint="Use terms like '2 x' or '-y' with + and - between terms.",
        )
    if s[0] not in "+-":
        s = "+" + s
    coeffs: dict[str, float] = {}
    const = 0.0
    for chunk in re.findall(r"[+-](?:[^+-]+)", s):
        m = _TERM.match(chunk)
        if not m:
            raise ParseError(
                f"cannot parse term in: {expr!r}",
                code="INVALID_TERM",
                context={"expression": expr},
            )
        sign = 1.0 if m.group(1) == "+" else -1.0
        if m.group(3) and m.group(2) is not None:
            coef = float(m.group(2)) if m.group(2) else 1.0
            var = m.group(3).lower()
            _merge_coeff(coeffs, var, sign * coef)
        elif m.group(4):
            const += sign * float(m.group(4))
        elif m.group(5):
            _merge_coeff(coeffs, m.group(5).lower(), sign * 1.0)
        else:
            raise ParseError(
                f"cannot parse term in: {expr!r}",
                code="INVALID_TERM",
                context={"expression": expr},
            )
    return coeffs, const


def _split_constraint(line: str) -> tuple[str, Sense, str]:
    m = re.search(r"(<=|>=|<|>|=)", line)
    if not m:
        raise ParseError(
            f"missing comparator in constraint: {line!r}",
            code="MISSING_COMPARATOR",
            hint="Each constraint must include <=, >=, =, <, or >.",
            context={"constraint": line},
        )
    op = m.group(1)
    assert op in ("<=", ">=", "<", ">", "=")
    left = line[: m.start()].strip()
    right = line[m.end() :].strip()
    if not left or not right:
        raise ParseError(
            f"invalid constraint: {line!r}",
            code="INVALID_CONSTRAINT",
            context={"constraint": line},
        )
    return left, op, right  # type: ignore[return-value]


def _normalize_constraint(left: str, sense: Sense, right: str, label: str) -> RawConstraint:
    lc, lk = parse_linear(left)
    rc, rk = parse_linear(right)
    coeffs: dict[str, float] = {}
    for v, c in lc.items():
        coeffs[v] = coeffs.get(v, 0.0) + c
    for v, c in rc.items():
        coeffs[v] = coeffs.get(v, 0.0) - c
    k0 = lk - rk
    if sense == "<=":
        return RawConstraint(coeffs=coeffs, rhs=-k0, sense="<=", label=label)
    if sense == "<":
        return RawConstraint(coeffs=coeffs, rhs=-k0 - STRICT_EPS, sense="<=", label=label)
    if sense == ">=":
        for v in list(coeffs.keys()):
            coeffs[v] = -coeffs[v]
        return RawConstraint(coeffs=coeffs, rhs=k0, sense="<=", label=label)
    if sense == ">":
        for v in list(coeffs.keys()):
            coeffs[v] = -coeffs[v]
        return RawConstraint(coeffs=coeffs, rhs=k0 - STRICT_EPS, sense="<=", label=label)
    if sense == "=":
        return RawConstraint(coeffs=coeffs, rhs=-k0, sense="=", label=label)
    raise ParseError("unknown sense")


_DOMAIN_ALIASES: dict[str, VarDomain] = {
    "continuous": "continuous",
    "cont": "continuous",
    "real": "continuous",
    "integer": "integer",
    "int": "integer",
    "binary": "binary",
    "bin": "binary",
    "bool": "binary",
}


def _parse_domain_declaration(line: str) -> tuple[str, VarDomain]:
    t = line.strip().rstrip(";")
    m = re.fullmatch(
        r"([a-z_][a-z0-9_]*)\s*(?::|=|\bis\b|\bin\b)?\s*([a-z_][a-z0-9_]*)",
        t,
        flags=re.IGNORECASE,
    )
    if not m:
        raise ParseError(
            f"invalid variable domain declaration: {line!r}",
            code="INVALID_DOMAIN_DECLARATION",
            hint="Use forms like `x integer`, `y: binary`, or `z continuous`.",
            context={"declaration": line},
        )
    var = m.group(1).lower()
    domain_token = m.group(2).lower()
    domain = _DOMAIN_ALIASES.get(domain_token)
    if domain is None:
        raise ParseError(
            f"unknown variable domain {domain_token!r}",
            code="UNKNOWN_VARIABLE_DOMAIN",
            hint="Supported domains are continuous, integer, and binary.",
            context={"declaration": line, "domain": domain_token, "variable": var},
        )
    return var, domain


def _parse_inline_declarations(spec: str) -> list[str]:
    t = spec.strip()
    if not t:
        return []
    return [part.strip() for part in t.split(",") if part.strip()]


def parse_lp_source(source: str) -> tuple[ParsedLP, list[str]]:
    lines: list[str] = []
    for raw in source.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            lines.append(line)

    if not lines:
        raise ParseError(
            "empty problem",
            code="EMPTY_PROBLEM",
            hint="Add a maximize/minimize objective and at least one constraint.",
        )

    obj_line_idx = None
    objective_sense: ObjSense | None = None
    for i, line in enumerate(lines):
        low = line.lower()
        if low.startswith("maximize") or low.startswith("max "):
            objective_sense = "maximize"
            obj_line_idx = i
            break
        if low.startswith("minimize") or low.startswith("min "):
            objective_sense = "minimize"
            obj_line_idx = i
            break
    if obj_line_idx is None or objective_sense is None:
        raise ParseError(
            "need a maximize or minimize line",
            code="MISSING_OBJECTIVE",
            hint="Start with `maximize ...` or `minimize ...`.",
        )

    obj_text = lines[obj_line_idx]
    low = obj_text.lower()
    if low.startswith("maximize"):
        expr = obj_text[len("maximize") :].strip()
    elif low.startswith("minimize"):
        expr = obj_text[len("minimize") :].strip()
    elif low.startswith("max "):
        expr = obj_text[4:].strip()
    elif low.startswith("min "):
        expr = obj_text[4:].strip()
    else:
        raise ParseError("invalid objective line", code="INVALID_OBJECTIVE_LINE")

    try:
        oc, _ok = parse_linear(expr)
    except ParseError as exc:
        raise ParseError(
            f"line {obj_line_idx + 1} (objective): {exc}",
            code=exc.code,
            hint=exc.hint,
            context={"line": obj_line_idx + 1, "section": "objective", **exc.context},
        ) from exc
    if not oc:
        raise ParseError(
            f"line {obj_line_idx + 1} (objective): must contain at least one variable",
            code="OBJECTIVE_NO_VARIABLES",
            hint="Include at least one variable term, e.g. `3 x`.",
            context={"line": obj_line_idx + 1, "section": "objective"},
        )

    subj_idx = None
    for j in range(obj_line_idx + 1, len(lines)):
        if re.fullmatch(r"(subject\s+to|s\.t\.|st)\s*:?", lines[j].lower()):
            subj_idx = j
            break
    if subj_idx is None:
        raise ParseError(
            'expected "subject to" (optional colon) after objective',
            code="MISSING_SUBJECT_TO",
            hint="After the objective line, add `subject to` then constraints.",
        )

    constraints: list[RawConstraint] = []
    plot_labels: list[str] = []

    modeling_notes: list[str] = []
    variable_domains: dict[str, VarDomain] = {}
    used_strict = False
    in_variables_block = False
    for line_no, line in enumerate(lines[subj_idx + 1 :], start=subj_idx + 2):
        low = line.lower()
        header_match = re.match(r"^(variables|vars)\b\s*:?\s*(.*)$", line, flags=re.IGNORECASE)
        if header_match:
            in_variables_block = True
            decls = _parse_inline_declarations(header_match.group(2))
            for decl in decls:
                try:
                    var, domain = _parse_domain_declaration(decl)
                except ParseError as exc:
                    raise ParseError(
                        f"line {line_no} ({decl!r}): {exc}",
                        code=exc.code,
                        hint=exc.hint,
                        context={"line": line_no, "section": "variables", **exc.context},
                    ) from exc
                if var in variable_domains and variable_domains[var] != domain:
                    raise ParseError(
                        f"line {line_no}: duplicate variable domain for {var!r}",
                        code="DUPLICATE_VARIABLE_DOMAIN",
                        hint="Declare each variable domain only once.",
                        context={
                            "line": line_no,
                            "section": "variables",
                            "variable": var,
                            "first_domain": variable_domains[var],
                            "second_domain": domain,
                        },
                    )
                variable_domains[var] = domain
            continue
        if in_variables_block and not re.search(r"(<=|>=|<|>|=)", line):
            decls = _parse_inline_declarations(line)
            for decl in decls:
                try:
                    var, domain = _parse_domain_declaration(decl)
                except ParseError as exc:
                    raise ParseError(
                        f"line {line_no} ({decl!r}): {exc}",
                        code=exc.code,
                        hint=exc.hint,
                        context={"line": line_no, "section": "variables", **exc.context},
                    ) from exc
                if var in variable_domains and variable_domains[var] != domain:
                    raise ParseError(
                        f"line {line_no}: duplicate variable domain for {var!r}",
                        code="DUPLICATE_VARIABLE_DOMAIN",
                        hint="Declare each variable domain only once.",
                        context={
                            "line": line_no,
                            "section": "variables",
                            "variable": var,
                            "first_domain": variable_domains[var],
                            "second_domain": domain,
                        },
                    )
                variable_domains[var] = domain
            continue
        in_variables_block = False
        raw_label = line.strip().rstrip(";")
        if not raw_label:
            continue
        try:
            left, sense, right = _split_constraint(raw_label)
            rc = _normalize_constraint(left, sense, right, raw_label)
        except ParseError as exc:
            raise ParseError(
                f"line {line_no} ({raw_label!r}): {exc}",
                code=exc.code,
                hint=exc.hint,
                context={"line": line_no, "section": "constraint", "constraint": raw_label, **exc.context},
            ) from exc
        if sense in ("<", ">"):
            used_strict = True
        constraints.append(rc)
        plot_labels.append(raw_label)
    if used_strict:
        modeling_notes.append(
            f"Strict inequalities were relaxed with epsilon={STRICT_EPS} for a closed feasible model."
        )

    return (
        ParsedLP(
            objective_sense=objective_sense,
            objective=oc,
            constraints=constraints,
            variable_domains=variable_domains,
            modeling_notes=modeling_notes,
        ),
        plot_labels,
    )
