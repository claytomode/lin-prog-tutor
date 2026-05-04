<script lang="ts">
  import {
    hasFeasibleSetSketch,
    isPolyhedron3d,
    plotObjectiveCaption,
  } from "$lib/lp/feasible.js";
  import { clearPlot, drawPlot } from "$lib/lp/plot.js";
  import type { AnalyzeResponse } from "$lib/lp/types.js";

  let {
    data,
    loading,
    activeStep,
    skipPlot3d,
  }: {
    data: AnalyzeResponse | null;
    loading: boolean;
    activeStep: number;
    skipPlot3d: boolean;
  } = $props();

  let plotDiv = $state<HTMLDivElement | null>(null);

  const sketchAvailable = $derived(
    data != null && hasFeasibleSetSketch(data, skipPlot3d),
  );

  const noSketchFallback =
    "This panel only sketches the feasible region in 1D (one variable), 2D (two variables), or 3D (three variables). The solver and tableau still use the full model.";

  $effect(() => {
    if (!plotDiv) return;
    if (!data) return;
    if (sketchAvailable) {
      void drawPlot(plotDiv, data, { activeStep, skipPlot3d });
    } else {
      void clearPlot(plotDiv);
    }
  });
</script>

<section class="panel grow plot-panel" class:plot-panel-loading={loading}>
  <div class="plot-head">
    <h2 class="panel-title">
      {#if data?.feasible_region && typeof data.feasible_region === "object" && "kind" in data.feasible_region && (data.feasible_region as { kind: string }).kind === "polyhedron_3d"}
        Feasible polyhedron (3D)
      {:else if data?.feasible_region && typeof data.feasible_region === "object" && "kind" in data.feasible_region && (data.feasible_region as { kind: string }).kind === "interval_1d"}
        Feasible interval
      {:else}
        Feasible set
      {/if}
    </h2>
    {#if data}
      {@const cap = plotObjectiveCaption(data)}
      {#if cap && sketchAvailable && (!isPolyhedron3d(data) || !skipPlot3d)}
        <p class="plot-sub hint-on">{cap}</p>
      {/if}
    {:else}
      <p class="plot-sub plot-sub-skeleton" class:sk-shimmer={loading} aria-hidden="true">
        <span class="sk-line sk-line-wide"></span>
      </p>
    {/if}
  </div>
  <div class="plot-wrap">
    {#if !data}
      <div class="plot-skeleton" class:sk-shimmer={loading} aria-hidden="true">
        <div class="plot-skeleton-inner">
          <div class="plot-skeleton-feasible"></div>
          <div class="plot-skeleton-axis"></div>
        </div>
      </div>
    {/if}
    <div class="plot-stack">
      <div class="plot" bind:this={plotDiv}></div>
      {#if data && !sketchAvailable}
        <div class="plot-empty-overlay" role="status">
          <p class="plot-empty-title">No region diagram</p>
          <p class="plot-empty-body">
            {data.geometry_note ?? noSketchFallback}
          </p>
        </div>
      {/if}
    </div>
    {#if loading}
      <div class="plot-busy" role="status" aria-live="polite">
        <span class="spinner" aria-hidden="true"></span>
        <span>Analyzing model&hellip;</span>
      </div>
    {/if}
  </div>
  {#if data && isPolyhedron3d(data) && skipPlot3d}
    <p class="muted small plot-note plot-skip-note">3D feasible region hidden for this session preset.</p>
  {/if}
  {#if data?.geometry_note && sketchAvailable}
    <p class="muted small plot-note hint-on">{data.geometry_note}</p>
  {/if}
</section>

<style>
  .panel-title {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0 0 0.85rem;
    color: var(--color-text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  .muted {
    color: var(--color-text-muted);
  }
  .small {
    font-size: 0.875rem;
    line-height: 1.5;
  }
  .grow {
    min-height: 380px;
  }
  .panel {
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 1.1rem 1.15rem 1.2rem;
    box-shadow: var(--shadow);
  }
  .plot-panel {
    background: var(--color-surface);
  }
  .plot-head {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-bottom: 0.65rem;
  }
  .plot-head .panel-title {
    margin: 0;
  }
  .plot-sub {
    margin: 0;
    max-width: 42rem;
    font-size: 0.88rem;
    line-height: 1.45;
    color: var(--color-text-muted);
  }
  .plot-note {
    margin: 0.55rem 0 0;
  }
  .plot-wrap {
    position: relative;
    min-height: 380px;
    overscroll-behavior: contain;
  }
  .plot-stack {
    position: relative;
    width: 100%;
    min-height: 380px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
    overflow: hidden;
    background: var(--plot-paper);
    touch-action: pan-x pan-y pinch-zoom;
    overscroll-behavior: contain;
  }
  .plot-stack .plot {
    position: relative;
    z-index: 1;
    width: 100%;
    min-height: 380px;
    border: none;
    border-radius: 0;
  }
  .plot-empty-overlay {
    position: absolute;
    inset: 0;
    z-index: 3;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.65rem;
    padding: 1.25rem 1.5rem;
    text-align: center;
    background: color-mix(in srgb, var(--plot-paper) 92%, var(--color-surface-raised));
    pointer-events: none;
  }
  .plot-empty-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    font-family: var(--font-serif);
    color: var(--color-text);
  }
  .plot-empty-body {
    margin: 0;
    max-width: 28rem;
    font-size: 0.9rem;
    line-height: 1.5;
    color: var(--color-text-muted);
  }
  .plot-panel-loading .plot-stack {
    opacity: 0.35;
    pointer-events: none;
  }
  .plot-busy {
    position: absolute;
    inset: 0;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.65rem;
    background: color-mix(in srgb, var(--color-surface-raised) 88%, transparent);
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--color-text-muted);
  }
  .spinner {
    width: 1.65rem;
    height: 1.65rem;
    border: 2px solid var(--color-border-strong);
    border-top-color: var(--color-accent);
    border-radius: 50%;
    animation: lp-spin 0.75s linear infinite;
  }
  @keyframes lp-spin {
    to {
      transform: rotate(360deg);
    }
  }
  .plot-sub-skeleton {
    margin: 0;
    min-height: 1.35rem;
    display: flex;
    align-items: center;
  }
  .plot-skeleton {
    position: absolute;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    border-radius: var(--radius-sm);
    background: color-mix(in srgb, var(--color-surface) 92%, var(--color-bg-deep));
  }
  .plot-skeleton-inner {
    position: absolute;
    inset: 10% 9% 12% 11%;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    gap: 0.45rem;
    border: 1px dashed color-mix(in srgb, var(--color-border) 75%, transparent);
    border-radius: 6px;
    padding: 0.5rem 0.55rem;
  }
  .plot-skeleton-feasible {
    flex: 1;
    min-height: 42%;
    border-radius: 5px;
    background: color-mix(in srgb, var(--color-border) 35%, var(--color-surface));
    opacity: 0.52;
    animation: none;
  }
  .plot-skeleton-axis {
    height: 0.55rem;
    border-radius: 4px;
    width: 72%;
    align-self: flex-end;
    background: color-mix(in srgb, var(--color-border) 55%, var(--color-bg-deep));
    opacity: 0.55;
    animation: none;
  }
  .plot-skeleton.sk-shimmer .plot-skeleton-feasible {
    animation: sk-pulse 1.35s ease-in-out infinite;
  }
  .plot-skeleton.sk-shimmer .plot-skeleton-axis {
    animation: sk-pulse 1.35s ease-in-out 0.15s infinite;
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
  .plot-sub-skeleton .sk-line {
    opacity: 0.5;
    animation: none;
  }
  .plot-sub-skeleton.sk-shimmer .sk-line {
    animation: sk-pulse 1.35s ease-in-out infinite;
  }
  @media (prefers-reduced-motion: reduce) {
    .plot-skeleton.sk-shimmer .plot-skeleton-feasible,
    .plot-skeleton.sk-shimmer .plot-skeleton-axis,
    .plot-sub-skeleton.sk-shimmer .sk-line {
      animation: none !important;
      opacity: 0.52;
    }
  }
</style>
