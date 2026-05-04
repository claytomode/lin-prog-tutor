export const defaultSource = `maximize 3 x + 2 y
subject to
x + y <= 4
x >= 0
y >= 0`;

export const PRESET_STORAGE_KEY = "lp-tutor-study-preset";

export type StudyPreset = "default" | "classroom" | "self-study";

export function presetFlags(p: StudyPreset): {
  compactTableau: boolean;
  skipPlot3d: boolean;
  hintsDefault: boolean;
} {
  if (p === "classroom") {
    return { compactTableau: true, skipPlot3d: true, hintsDefault: false };
  }
  if (p === "self-study") {
    return { compactTableau: false, skipPlot3d: false, hintsDefault: true };
  }
  return { compactTableau: false, skipPlot3d: false, hintsDefault: true };
}
