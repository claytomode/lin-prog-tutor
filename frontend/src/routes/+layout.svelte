<script lang="ts">
  import { resolveRoute } from "$app/paths";
  import "../app.css";

  let { children } = $props();
</script>

<svelte:head>
  <title>LP Tutor</title>
  <meta name="description" content="Parse, solve, and visualize small linear programs." />
</svelte:head>

<div class="shell">
  <nav class="site-nav" aria-label="Primary">
    <a href={resolveRoute("/", {})} class="brand">LP Tutor</a>
    <div class="site-nav-links">
      <a href={resolveRoute("/", {})}>Solver</a>
      <a href={resolveRoute("/docs", {})}>Docs</a>
    </div>
  </nav>
  {@render children()}
</div>

<style>
  .shell {
    max-width: 1120px;
    margin: 0 auto;
    padding: clamp(1.25rem, 4vw, 2.25rem) clamp(1rem, 3vw, 1.5rem) 3rem;
  }
  .site-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 1rem;
  }
  .site-nav-links {
    display: flex;
    gap: 0.8rem;
  }
  .site-nav a {
    text-decoration: none;
    font-weight: 560;
    color: var(--color-accent);
  }
  .site-nav a:hover {
    text-decoration: underline;
  }
  .brand {
    font-family: var(--font-serif);
    font-size: 1.2rem;
  }
</style>
