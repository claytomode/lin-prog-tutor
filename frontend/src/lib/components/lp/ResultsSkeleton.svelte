<script lang="ts">
  let { loading }: { loading: boolean } = $props();
</script>

<div class="sk-placeholder-root" class:sk-shimmer={loading}>
  <section class="panel sk-panel solution-skeleton" aria-hidden="true">
    <div class="sk-title"></div>
    <div class="sk-stack">
      <div class="sk-line sk-line-wide"></div>
      <div class="sk-line sk-line-medium"></div>
      <div class="sk-line sk-line-narrow"></div>
    </div>
  </section>
  <section class="panel sk-panel tutor-skeleton" aria-hidden="true">
    <div class="sk-title sk-title-short"></div>
    <div class="sk-step-pill"></div>
    <div class="sk-step-pill sk-step-pill-delay"></div>
  </section>
  <section class="panel sk-panel tableau-skeleton" aria-hidden="true">
    <div class="sk-tableau-top">
      <div class="sk-title sk-title-medium"></div>
      <div class="sk-stepbar">
        <div class="sk-chip"></div>
        <div class="sk-chip sk-chip-wide"></div>
        <div class="sk-chip"></div>
      </div>
    </div>
    <div class="sk-line sk-line-wide sk-gap-top"></div>
    <div class="sk-table-rows">
      {#each [0, 1, 2, 3, 4, 5] as r (r)}
        <div class="sk-table-row" style="--sk-i: {r}"></div>
      {/each}
    </div>
  </section>
</div>

<style>
  .panel {
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 1.1rem 1.15rem 1.2rem;
    box-shadow: var(--shadow);
  }
  .sk-placeholder-root {
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
  }
  .sk-panel {
    min-height: 0;
  }
  .solution-skeleton {
    min-height: 7.5rem;
  }
  .tutor-skeleton {
    min-height: 9.5rem;
  }
  .tutor-skeleton .sk-step-pill {
    max-width: none;
  }
  .tableau-skeleton {
    min-height: 18rem;
  }
  .sk-title {
    height: 1.05rem;
    width: 6.5rem;
    border-radius: 5px;
    background: color-mix(in srgb, var(--color-border) 50%, var(--color-bg-deep));
    opacity: 0.54;
    animation: none;
  }
  .sk-title-short {
    width: 5rem;
  }
  .sk-title-medium {
    width: 9rem;
  }
  .sk-stack {
    margin-top: 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .sk-line {
    height: 0.68rem;
    border-radius: 4px;
    background: color-mix(in srgb, var(--color-border) 45%, var(--color-bg-deep));
    opacity: 0.52;
    animation: none;
  }
  .sk-line-wide {
    width: min(100%, 22rem);
  }
  .sk-line-medium {
    width: min(100%, 15rem);
  }
  .sk-line-narrow {
    width: min(100%, 9rem);
  }
  .sk-gap-top {
    margin-top: 0.75rem;
  }
  .sk-step-pill {
    margin-top: 0.65rem;
    height: 2.65rem;
    max-width: 30rem;
    width: 100%;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
    background: color-mix(in srgb, var(--color-surface) 70%, var(--color-bg-deep));
    opacity: 0.5;
    animation: none;
  }
  .sk-step-pill-delay {
    opacity: 0.48;
  }
  .sk-tableau-top {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 0.75rem 1rem;
    margin-bottom: 0.35rem;
  }
  .sk-stepbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.55rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
    background: var(--color-bg-deep);
  }
  .sk-chip {
    height: 1.85rem;
    width: 5.5rem;
    border-radius: var(--radius-sm);
    background: color-mix(in srgb, var(--color-border) 40%, var(--color-surface-raised));
    opacity: 0.52;
    animation: none;
  }
  .sk-chip-wide {
    width: 8.5rem;
  }
  .sk-table-rows {
    margin-top: 0.65rem;
    display: flex;
    flex-direction: column;
    gap: 0.38rem;
  }
  .sk-table-row {
    height: 0.95rem;
    width: 100%;
    border-radius: 4px;
    background: color-mix(in srgb, var(--color-border) 38%, var(--color-bg-deep));
    opacity: 0.5;
    animation: none;
  }
  @keyframes sk-pulse {
    0%,
    100% {
      opacity: 0.42;
    }
    50% {
      opacity: 0.78;
    }
  }
  .sk-placeholder-root.sk-shimmer .sk-title,
  .sk-placeholder-root.sk-shimmer .sk-line,
  .sk-placeholder-root.sk-shimmer .sk-step-pill,
  .sk-placeholder-root.sk-shimmer .sk-chip,
  .sk-placeholder-root.sk-shimmer .sk-table-row {
    animation: sk-pulse 1.35s ease-in-out infinite;
  }
  .sk-placeholder-root.sk-shimmer .sk-line-medium {
    animation-delay: 0.08s;
  }
  .sk-placeholder-root.sk-shimmer .sk-line-narrow {
    animation-delay: 0.16s;
  }
  .sk-placeholder-root.sk-shimmer .sk-step-pill {
    animation-delay: 0.05s;
  }
  .sk-placeholder-root.sk-shimmer .sk-step-pill-delay {
    animation-delay: 0.12s;
  }
  .sk-placeholder-root.sk-shimmer .sk-chip-wide {
    animation-delay: 0.1s;
  }
  .sk-placeholder-root.sk-shimmer .sk-table-row {
    animation-delay: calc(0.04s * var(--sk-i, 0));
  }
  @media (prefers-reduced-motion: reduce) {
    .sk-placeholder-root.sk-shimmer .sk-title,
    .sk-placeholder-root.sk-shimmer .sk-line,
    .sk-placeholder-root.sk-shimmer .sk-step-pill,
    .sk-placeholder-root.sk-shimmer .sk-chip,
    .sk-placeholder-root.sk-shimmer .sk-table-row {
      animation: none !important;
      opacity: 0.52;
    }
  }
</style>
