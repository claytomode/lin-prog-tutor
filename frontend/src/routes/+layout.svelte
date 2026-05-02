<script lang="ts">
  import "../app.css";

  let { children } = $props();
</script>

<svelte:head>
  <title>LP Tutor</title>
  <meta name="description" content="Parse, solve, and visualize small linear programs." />
</svelte:head>

<div class="shell">
  {@render children()}
</div>

<style>
  .shell {
    max-width: 1120px;
    margin: 0 auto;
    padding: clamp(1.25rem, 4vw, 2.25rem) clamp(1rem, 3vw, 1.5rem) 3rem;
  }
</style>
