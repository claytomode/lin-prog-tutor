type HumanizeApiErrorInput = {
  code?: string | null;
  message?: string | null;
  hint?: string | null;
};

/** Map stable backend error codes to friendlier UI copy. */
export function humanizeApiError({ code, message, hint }: HumanizeApiErrorInput): string {
  if (hint) return hint;

  const byCode: Record<string, string> = {
    EMPTY_PROBLEM: "The source is empty after comments. Add a maximize/minimize objective and constraints.",
    MISSING_OBJECTIVE: "Start with a line like `maximize 3 x + 2 y` or `minimize x + y`.",
    MISSING_SUBJECT_TO:
      'After the objective, add a line `subject to` (or `s.t.`), then one constraint per line.',
    MISSING_COMPARATOR:
      "Each constraint needs a comparator: <=, >=, =, <, or > between the left and right sides.",
    NON_LINEAR_EXPRESSION:
      "Only linear sums are allowed: use `2 x` or `-y`, not `*`, `/`, or powers.",
    INVALID_TERM:
      "A term could not be parsed. Use forms like `3 x`, `x`, or `-0.5 y`, with explicit +/− between terms.",
    OBJECTIVE_NO_VARIABLES: "The objective must include at least one variable term.",
    NO_VARIABLES: "No variables were found. Add variables to the objective and constraints.",
    INVALID_DOMAIN_DECLARATION:
      "A variable domain declaration is invalid. Use forms like `x integer`, `y: binary`, or `z continuous`.",
    UNKNOWN_VARIABLE_DOMAIN:
      "Unsupported variable domain. Allowed values are `continuous`, `integer`, or `binary`.",
    DUPLICATE_VARIABLE_DOMAIN:
      "A variable domain was declared more than once. Keep one declaration per variable.",
    PROBLEM_CLASS_MISMATCH:
      "Problem class is set to LP, but integer/binary variable domains were declared.",
    UNKNOWN_DOMAIN_VARIABLE:
      "The domain list names a variable that does not appear in the objective or constraints.",
    MIP_NOT_IMPLEMENTED:
      "The API returned MIP_NOT_IMPLEMENTED. Restart the dev servers from the project root (`bun run dev`) so the backend loads the SciPy MILP solver.",
    MIP_SOLVER_ERROR:
      "The mixed-integer solver hit an internal error. Try simplifying the model or check constraints for inconsistency.",
    MODEL_ERROR: "The model could not be processed. Check the formulation and try again.",
    PARSE_ERROR: "The LP source could not be parsed. Check syntax and try again.",
  };
  if (code && byCode[code]) return byCode[code];
  if (message) return message;
  return "Request failed. Please review the model and try again.";
}
