import { error } from "@sveltejs/kit";
import { docsChapters, getChapterBySlug } from "$lib/docs/chapters.js";
import type { PageLoad } from "./$types";

export const load: PageLoad = ({ params }) => {
  const chapter = getChapterBySlug(params.slug);
  if (!chapter) {
    error(404, "Chapter not found");
  }

  const index = docsChapters.findIndex((item) => item.slug === chapter.slug);

  return {
    chapter,
    prev: index > 0 ? docsChapters[index - 1] : null,
    next: index < docsChapters.length - 1 ? docsChapters[index + 1] : null,
  };
};
