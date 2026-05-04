import errorCodeGlossaryMarkdown from "./content/error-code-glossary.md?raw";
import furtherReadingMarkdown from "./content/further-reading.md?raw";
import integerIntroMarkdown from "./content/intro-to-integer-optimization.md?raw";
import lpVsIpMarkdown from "./content/lp-vs-ip-vs-milp.md?raw";
import modelingPitfallsMarkdown from "./content/modeling-pitfalls.md?raw";
import primalDualMarkdown from "./content/primal-and-dual.md?raw";
import solvingLpsMarkdown from "./content/solving-lps-in-this-app.md?raw";
import whatIsLpMarkdown from "./content/what-is-an-lp.md?raw";
import { renderMarkdownToHtml } from "./markdown.js";

export type DocsChapter = {
  slug: string;
  title: string;
  description: string;
  markdown: string;
  html: string;
};

type ChapterSource = Omit<DocsChapter, "html">;

const chapterSources: ChapterSource[] = [
  {
    slug: "what-is-an-lp",
    title: "What is an LP?",
    description: "Intuition plus a formal linear programming definition.",
    markdown: whatIsLpMarkdown,
  },
  {
    slug: "lp-vs-ip-vs-milp",
    title: "LP vs IP vs MILP",
    description: "How continuous and integer models differ in structure and difficulty.",
    markdown: lpVsIpMarkdown,
  },
  {
    slug: "primal-and-dual",
    title: "Primal and Dual",
    description: "Dual interpretation, weak/strong duality, and why dual prices matter.",
    markdown: primalDualMarkdown,
  },
  {
    slug: "solving-lps-in-this-app",
    title: "Solving LPs in this app",
    description: "Parser, solver, plots, tableau, and how they fit together.",
    markdown: solvingLpsMarkdown,
  },
  {
    slug: "modeling-pitfalls",
    title: "Modeling pitfalls",
    description: "Strict inequalities, domains, and MILP expectations.",
    markdown: modelingPitfallsMarkdown,
  },
  {
    slug: "intro-to-integer-optimization",
    title: "Intro to integer optimization",
    description: "LP relaxation and branch-and-bound at a concept level.",
    markdown: integerIntroMarkdown,
  },
  {
    slug: "further-reading",
    title: "Further reading",
    description: "Curated references for deeper study.",
    markdown: furtherReadingMarkdown,
  },
  {
    slug: "error-code-glossary",
    title: "Error code glossary",
    description: "Stable API error codes and how to fix the underlying issue.",
    markdown: errorCodeGlossaryMarkdown,
  },
];

export const docsChapters: DocsChapter[] = chapterSources.map((chapter) => ({
  ...chapter,
  html: renderMarkdownToHtml(chapter.markdown),
}));

export function getChapterBySlug(slug: string): DocsChapter | undefined {
  return docsChapters.find((chapter) => chapter.slug === slug);
}
