import { marked } from "marked";
import markedKatex from "marked-katex-extension";
import sanitizeHtml from "sanitize-html";

marked.use(
  markedKatex({
    throwOnError: false,
    nonStandard: true,
  }),
);

marked.setOptions({
  gfm: true,
});

export function renderMarkdownToHtml(markdown: string): string {
  const rawHtml = marked.parse(markdown) as string;
  return sanitizeHtml(rawHtml, {
    allowedTags: [
      ...sanitizeHtml.defaults.allowedTags,
      "h1",
      "h2",
      "img",
      "span",
      "math",
      "annotation",
      "semantics",
      "mrow",
      "mi",
      "mn",
      "mo",
      "msup",
      "msub",
      "mfrac",
      "msqrt",
      "mspace",
    ],
    allowedAttributes: {
      ...sanitizeHtml.defaults.allowedAttributes,
      span: ["class", "style"],
      div: ["class"],
      code: ["class"],
      a: ["href", "name", "target", "rel"],
      img: ["src", "alt", "title", "width", "height"],
      math: ["xmlns", "display"],
      annotation: ["encoding"],
      semantics: [],
      mrow: [],
      mi: [],
      mn: [],
      mo: [],
      msup: [],
      msub: [],
      mfrac: [],
      msqrt: [],
      mspace: [],
    },
  });
}
