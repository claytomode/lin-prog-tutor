import type { components } from "$lib/api/openapi";

type Schemas = components["schemas"];

export type AnalyzeRequest = Schemas["AnalyzeRequest"];
export type AnalyzeResponse = Schemas["AnalyzeResponse"];

export type TableauMode = AnalyzeRequest["tableau_mode"];
export type TutorStep = Schemas["TutorStep"];
export type Feasible2D = Schemas["FeasibleRegion2D"];
export type TableauStep = Schemas["TableauStep"];
export type TableauWalkthrough = Schemas["TableauWalkthrough"];
export type Constraint2d = Schemas["ConstraintPlot2D"];
