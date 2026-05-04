<script lang="ts">
  import { resolveRoute } from "$app/paths";
  import { page } from "$app/state";

  let { data, children } = $props();
</script>

<section class="docs-shell">
  <aside class="docs-nav">
    <p class="docs-nav-label">Textbook</p>
    <h1>Linear Optimization Notes</h1>
    <a href={resolveRoute("/docs", {})} class={page.url.pathname === "/docs" ? "active" : ""}>Overview</a>
    {#each data.chapters as chapter (chapter.slug)}
      <a
        href={resolveRoute("/docs/[slug]", { slug: chapter.slug })}
        class={page.url.pathname === `/docs/${chapter.slug}` ? "active" : ""}
      >
        {chapter.title}
      </a>
    {/each}
  </aside>

  <div class="docs-content">
    {@render children()}
  </div>
</section>

<style>
  .docs-shell {
    display: grid;
    gap: 1.2rem;
  }

  @media (min-width: 980px) {
    .docs-shell {
      grid-template-columns: minmax(16rem, 20rem) minmax(0, 1fr);
      align-items: start;
    }
  }

  .docs-nav {
    position: sticky;
    top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 1rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    background: var(--color-surface);
  }

  .docs-nav h1 {
    margin: 0;
    font-family: var(--font-serif);
    font-size: 1.2rem;
    line-height: 1.2;
  }

  .docs-nav-label {
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.75rem;
    color: var(--color-text-faint);
    font-weight: 650;
  }

  .docs-nav a {
    color: var(--color-accent);
    text-decoration: none;
    border-radius: var(--radius-sm);
    padding: 0.32rem 0.45rem;
  }

  .docs-nav a:hover {
    background: var(--color-bg-deep);
  }

  .docs-nav a.active {
    background: var(--color-accent);
    color: #fff;
  }

  .docs-content {
    min-width: 0;
  }
</style>
