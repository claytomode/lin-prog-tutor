<script lang="ts">
  import { resolveRoute } from "$app/paths";
  let { data } = $props();
</script>

<article class="docs-overview">
  <h2>Docs overview</h2>
  <p>
    This section is a lightweight textbook foundation for linear and integer optimization. Chapters are
    markdown-backed and rendered with LaTeX-style math.
  </p>

  <ul>
    {#each data.chapters as chapter (chapter.slug)}
      <li>
        <a href={resolveRoute("/docs/[slug]", { slug: chapter.slug })}>{chapter.title}</a>
        <p>{chapter.description}</p>
      </li>
    {/each}
  </ul>
</article>

<style>
  .docs-overview {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: clamp(1rem, 2vw, 1.4rem);
  }

  h2 {
    margin-top: 0;
    font-family: var(--font-serif);
    font-size: clamp(1.4rem, 3vw, 1.8rem);
  }

  ul {
    margin: 1rem 0 0;
    padding-left: 1.2rem;
  }

  li + li {
    margin-top: 0.75rem;
  }

  li p {
    margin: 0.25rem 0 0;
    color: var(--color-text-muted);
  }
</style>
