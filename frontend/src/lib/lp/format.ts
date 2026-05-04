import type { Constraint2d } from "./types.js";

export function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function fmtLin2d(v: number): string {
  if (!Number.isFinite(v)) return "?";
  const a = Math.abs(v);
  if (a < 1e-10) return "0";
  if (Number.isInteger(v)) return String(v);
  return v.toFixed(4).replace(/\.?0+$/, "");
}

/** Human-readable boundary line for 2D constraint hover. */
export function constraintHoverText(c: Constraint2d, x0: string, x1: string): string {
  let lhs = `${fmtLin2d(c.a)}·${x0} + ${fmtLin2d(c.b)}·${x1}`;
  lhs = lhs.replace(/\+ -/g, "− ").replace(/\+ \+/g, "+ ");
  const sym = c.sense === "<=" ? "≤" : c.sense === ">=" ? "≥" : "=";
  return `<b>${escapeHtml(c.label.replace(/\s+/g, " ").trim())}</b><br>${lhs} ${sym} ${fmtLin2d(c.rhs)}`;
}

export function shortLegend(s: string, max = 22): string {
  const t = s.replace(/\s+/g, " ").trim();
  return t.length <= max ? t : `${t.slice(0, max - 1)}…`;
}

/** Readable tableau coefficients; wide values use scientific notation so cells stay scannable. */
export function formatTableauCell(value: number): string {
  if (!Number.isFinite(value)) return "—";
  const ax = Math.abs(value);
  if (ax === 0) return "0";
  if (ax >= 1e4 || (ax > 0 && ax < 1e-3)) return value.toPrecision(4);
  if (ax >= 1000) return value.toFixed(1);
  if (Number.isInteger(value) && ax < 1e3) return String(value);
  return value.toFixed(2);
}

export function formatRatio(value: number): string {
  if (!Number.isFinite(value)) return "—";
  const ax = Math.abs(value);
  if (ax === 0) return "0";
  if (ax >= 1e4 || (ax > 0 && ax < 1e-4)) return value.toPrecision(4);
  if (ax >= 100) return value.toFixed(2);
  return value.toFixed(4);
}

export function isDualRatioNarrative(narrative: string): boolean {
  const t = narrative.toLowerCase();
  return t.includes("dual pivot") || t.includes("dual ratio test");
}

export function tableauRowLabel(
  rowIndex: number,
  numRows: number,
  basisLabels: string[],
): string {
  if (rowIndex < numRows - 1) return basisLabels[rowIndex] ?? "";
  return "z";
}
