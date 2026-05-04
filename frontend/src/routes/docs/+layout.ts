import type { LayoutLoad } from "./$types";
import { docsChapters } from "$lib/docs/chapters.js";

export const load: LayoutLoad = () => {
  return {
    chapters: docsChapters.map(({ slug, title, description }) => ({
      slug,
      title,
      description,
    })),
  };
};
