import { describe, expect, it } from "bun:test";
import { humanizeApiError } from "./api-errors.js";

describe("humanizeApiError", () => {
  it("prefers backend hint when present", () => {
    const msg = humanizeApiError({
      code: "EMPTY_PROBLEM",
      hint: "Custom backend hint",
      message: "fallback",
    });
    expect(msg).toBe("Custom backend hint");
  });

  it("maps known error code to friendly message", () => {
    const msg = humanizeApiError({
      code: "MISSING_OBJECTIVE",
      message: "need a maximize or minimize line",
    });
    expect(msg).toContain("Start with");
    expect(msg).toContain("maximize");
  });

  it("falls back to backend message for unknown code", () => {
    const msg = humanizeApiError({
      code: "SOMETHING_NEW",
      message: "backend says no",
    });
    expect(msg).toBe("backend says no");
  });

  it("uses final generic fallback when no fields provided", () => {
    const msg = humanizeApiError({});
    expect(msg).toContain("Request failed");
  });

  it("maps UNKNOWN_DOMAIN_VARIABLE", () => {
    const msg = humanizeApiError({
      code: "UNKNOWN_DOMAIN_VARIABLE",
      message: "variable_domains references unknown variable",
    });
    expect(msg).toContain("does not appear");
  });

  it("maps MIP_SOLVER_ERROR", () => {
    const msg = humanizeApiError({ code: "MIP_SOLVER_ERROR", message: "err" });
    expect(msg).toContain("mixed-integer");
  });
});
