from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Sense = Literal["<=", ">=", "="]
ObjSense = Literal["maximize", "minimize"]


class ParseError(ValueError):
    pass


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
    s = re.sub(r"\s+", "", expr.strip().lower())
    if not s:
        raise ParseError("empty expression")
    if re.search(r"[\^*/]", s):
        raise ParseError("only linear expressions are allowed (no *, /, powers)")
    if s[0] not in "+-":
        s = "+" + s
    coeffs: dict[str, float] = {}
    const = 0.0
    for chunk in re.findall(r"[+-](?:[^+-]+)", s):
        m = _TERM.match(chunk)
        if not m:
            raise ParseError(f"cannot parse term in: {expr!r}")
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
            raise ParseError(f"cannot parse term in: {expr!r}")
    return coeffs, const


def _split_constraint(line: str) -> tuple[str, Sense, str]:
    m = re.search(r"(<=|>=|=)", line)
    if not m:
        raise ParseError(f"missing comparator in constraint: {line!r}")
    op = m.group(1)
    assert op in ("<=", ">=", "=")
    left = line[: m.start()].strip()
    right = line[m.end() :].strip()
    if not left or not right:
        raise ParseError(f"invalid constraint: {line!r}")
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
    if sense == ">=":
        for v in list(coeffs.keys()):
            coeffs[v] = -coeffs[v]
        return RawConstraint(coeffs=coeffs, rhs=k0, sense="<=", label=label)
    if sense == "=":
        return RawConstraint(coeffs=coeffs, rhs=-k0, sense="=", label=label)
    raise ParseError("unknown sense")


def parse_lp_source(source: str) -> tuple[ParsedLP, list[str]]:
    lines: list[str] = []
    for raw in source.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            lines.append(line)

    if not lines:
        raise ParseError("empty problem")

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
        raise ParseError("need a maximize or minimize line")

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
        raise ParseError("invalid objective line")

    oc, _ok = parse_linear(expr)
    if not oc:
        raise ParseError("objective must contain at least one variable")

    subj_idx = None
    for j in range(obj_line_idx + 1, len(lines)):
        if re.fullmatch(r"subject\s+to|s\.t\.|st", lines[j].lower()):
            subj_idx = j
            break
    if subj_idx is None:
        raise ParseError('expected "subject to" after objective')

    constraints: list[RawConstraint] = []
    plot_labels: list[str] = []

    for line in lines[subj_idx + 1 :]:
        low = line.lower()
        if low.startswith("variables") or low.startswith("vars"):
            continue
        left, sense, right = _split_constraint(line)
        raw_label = line.strip()
        rc = _normalize_constraint(left, sense, right, raw_label)
        constraints.append(rc)
        plot_labels.append(raw_label)

    return ParsedLP(objective_sense=objective_sense, objective=oc, constraints=constraints), plot_labels
