import furtherReadingMarkdown from "./content/further-reading.md?raw";
import integerIntroMarkdown from "./content/intro-to-integer-optimization.md?raw";
import lpVsIpMarkdown from "./content/lp-vs-ip-vs-milp.md?raw";
import primalDualMarkdown from "./content/primal-and-dual.md?raw";
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
];

export const docsChapters: DocsChapter[] = chapterSources.map((chapter) => ({
  ...chapter,
  html: renderMarkdownToHtml(chapter.markdown),
}));

export function getChapterBySlug(slug: string): DocsChapter | undefined {
  return docsChapters.find((chapter) => chapter.slug === slug);
}
