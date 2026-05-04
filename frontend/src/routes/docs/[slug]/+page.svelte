<script lang="ts">
  import { resolveRoute } from "$app/paths";
  import "katex/dist/katex.min.css";

  let { data } = $props();
</script>

<article class="chapter">
  <header class="chapter-header">
    <h2>{data.chapter.title}</h2>
    <p>{data.chapter.description}</p>
  </header>

  <div class="chapter-body">
    {@html data.chapter.html}
  </div>

  <nav class="chapter-nav" aria-label="Chapter navigation">
    {#if data.prev}
      <a href={resolveRoute("/docs/[slug]", { slug: data.prev.slug })}>Previous: {data.prev.title}</a>
    {:else}
      <a href={resolveRoute("/docs", {})} aria-disabled={true}>Back to overview</a>
    {/if}
    {#if data.next}
      <a href={resolveRoute("/docs/[slug]", { slug: data.next.slug })}>Next: {data.next.title}</a>
    {/if}
  </nav>
</article>

<style>
  .chapter {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: clamp(1rem, 2vw, 1.5rem);
  }

  .chapter-header h2 {
    margin: 0;
    font-family: var(--font-serif);
    font-size: clamp(1.4rem, 3vw, 1.95rem);
    line-height: 1.15;
  }

  .chapter-header p {
    margin: 0.55rem 0 0;
    color: var(--color-text-muted);
  }

  .chapter-body {
    margin-top: 1.15rem;
  }

  .chapter-body :global(h2),
  .chapter-body :global(h3) {
    font-family: var(--font-serif);
    line-height: 1.25;
    margin: 1.3rem 0 0.55rem;
  }

  .chapter-body :global(p),
  .chapter-body :global(li) {
    line-height: 1.65;
  }

  .chapter-body :global(pre) {
    overflow-x: auto;
    padding: 0.75rem 0.85rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    background: var(--color-bg-deep);
  }

  .chapter-body :global(pre code) {
    display: block;
    padding: 0;
    border: none;
    border-radius: 0;
    background: transparent;
    font-size: 0.85rem;
    line-height: 1.55;
    white-space: pre;
  }

  .chapter-nav {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--color-border);
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .chapter-nav a[aria-disabled="true"] {
    opacity: 0.65;
    pointer-events: none;
  }
</style>
