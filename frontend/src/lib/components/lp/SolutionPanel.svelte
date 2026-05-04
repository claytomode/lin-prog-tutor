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
  {#if data.problem_class || data.is_mip != null}
    <p class="small meta-row">
      {#if data.problem_class}
        Class: <code>{data.problem_class}</code>
      {/if}
      {#if data.is_mip != null}
        {#if data.problem_class}&nbsp;&middot;&nbsp;{/if}
        MIP: <code>{data.is_mip ? "yes" : "no"}</code>
      {/if}
    </p>
  {/if}
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
  {#if data.is_mip && data.mip_method}
    <p class="muted small mip-method">
      MILP request path: <code>{data.mip_method}</code>
    </p>
  {/if}
  {#if data.is_mip && data.mip_diagnostics && Object.keys(data.mip_diagnostics).length > 0}
    <p class="muted small mip-diag">
      MIP diagnostics:
      <code>{JSON.stringify(data.mip_diagnostics)}</code>
    </p>
  {/if}
  {#if data.mip_gap != null || data.mip_node_count != null || data.mip_time_limit_hit != null}
    <p class="muted small mip-meta">
      {#if data.mip_gap != null}
        Gap: <code>{data.mip_gap}</code>
      {/if}
      {#if data.mip_node_count != null}
        {#if data.mip_gap != null}&nbsp;&middot;&nbsp;{/if}
        Nodes: <code>{data.mip_node_count}</code>
      {/if}
      {#if data.mip_time_limit_hit != null}
        {#if data.mip_gap != null || data.mip_node_count != null}&nbsp;&middot;&nbsp;{/if}
        Time limit: <code>{data.mip_time_limit_hit ? "hit" : "no"}</code>
      {/if}
    </p>
  {/if}
  {#if data.problem?.is_mip}
    <p class="muted small mip-note">
      Graphical two-/three-dimensional tutor steps and the simplex tableau follow <strong>continuous</strong> LP
      pedagogy. They are hidden for mixed-integer models until dedicated MIP tutor paths exist.
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
  .meta-row {
    margin: 0 0 0.25rem;
  }
  .mip-diag code,
  .mip-meta code {
    font-size: 0.82em;
    word-break: break-word;
  }
  .mip-note {
    max-width: 44rem;
    margin-top: 0.65rem !important;
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
