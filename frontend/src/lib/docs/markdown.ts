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

/**
 * `marked-katex-extension` only tokenizes `$...$` / `$$...$$`, not LaTeX `\(...\)` / `\[...\]`.
 * Normalize so chapter markdown can use either style.
 */
function normalizeLatexDelimiters(markdown: string): string {
  return markdown
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, inner: string) => `$$\n${inner.trim()}\n$$`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, inner: string) => `$${inner.trim()}$`);
}

export function renderMarkdownToHtml(markdown: string): string {
  const rawHtml = marked.parse(normalizeLatexDelimiters(markdown)) as string;
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
