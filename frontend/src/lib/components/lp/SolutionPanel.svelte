<script lang="ts">
  import type { AnalyzeResponse } from "$lib/lp/types.js";

  let {
    data,
    solutionHeadingEl = $bindable<HTMLHeadingElement | null>(null),
  }: {
    data: AnalyzeResponse;
    solutionHeadingEl?: HTMLHeadingElement | null;
  } = $props();
</script>

<section class="panel solution">
  <h2 class="panel-title" tabindex="-1" bind:this={solutionHeadingEl}>Solution</h2>
  <p>
    Status: <code>{data.solve_status}</code>
    {#if data.optimal_value != null}
      &nbsp;&middot;&nbsp; Objective: <code>{data.optimal_value.toFixed(6)}</code>
    {/if}
  </p>
  {#if data.optimal_point}
    <p class="small">
      Point:
      {#each Object.entries(data.optimal_point) as [k, v] (k)}
        <code>{k} = {v.toFixed(6)}</code>
        &nbsp;
      {/each}
    </p>
  {/if}
  {#if data.tableau_status === "ok" && data.tableau_verified != null}
    <p
      class="small tableau-verify"
      class:tableau-verify-ok={data.tableau_verified}
      class:tableau-verify-bad={!data.tableau_verified}
    >
      {#if data.tableau_verified}
        Tableau cross-check: final basis feasible solution matches HiGHS optimal value and constraints
        (within tolerance).
      {:else}
        Tableau cross-check failed. {data.tableau_verify_message ?? ""}
      {/if}
    </p>
    {#if data.tableau_verified && data.tableau_verify_message}
      <p class="muted small tableau-verify-note">{data.tableau_verify_message}</p>
    {/if}
  {/if}
</section>

<style>
  .panel-title {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0 0 0.85rem;
    color: var(--color-text);
  }
  .panel {
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 1.1rem 1.15rem 1.2rem;
    box-shadow: var(--shadow);
  }
  .muted {
    color: var(--color-text-muted);
  }
  .small {
    font-size: 0.875rem;
    line-height: 1.5;
  }
  .solution :global(p) {
    margin: 0.35rem 0 0;
  }
  .tableau-verify {
    margin: 0.65rem 0 0;
    font-weight: 600;
    line-height: 1.45;
  }
  .tableau-verify-ok {
    color: var(--color-text-muted);
  }
  .tableau-verify-bad {
    color: var(--color-danger);
  }
  .tableau-verify-note {
    margin: 0.35rem 0 0;
    max-width: 48rem;
  }
</style>
