<script lang="ts">
  import {
    formatRatio,
    formatTableauCell,
    isDualRatioNarrative,
    tableauRowLabel,
  } from "$lib/lp/format.js";
  import type { TableauWalkthrough as TableauWalkthroughT } from "$lib/lp/types.js";

  let {
    walkthrough: tw,
    compactTableau,
    tableauStep = $bindable(0),
  }: {
    walkthrough: TableauWalkthroughT;
    compactTableau: boolean;
    tableauStep: number;
  } = $props();

  let st = $derived(tw.steps[tableauStep]);
</script>

<section class="panel tableau-panel tableau-panel-bottom" class:tableau-compact={compactTableau}>
  <div class="tableau-head">
    <h2 class="panel-title tableau-title">
      Tableau <span class="tag">{tw.outcome}</span>
      <span class="muted small tableau-sense">Tableau sense: {tw.sense_for_tableau}</span>
    </h2>
    <div class="tableau-step-bar">
      <button
        type="button"
        class="ghost tableau-step-btn"
        disabled={tableauStep <= 0}
        aria-label="Previous tableau step"
        onclick={() => (tableauStep = Math.max(0, tableauStep - 1))}>← Prev</button>
      <span class="tableau-step-label"
        >Step <strong>{tableauStep + 1}</strong> of <strong>{tw.steps.length}</strong></span
      >
      <button
        type="button"
        class="ghost tableau-step-btn"
        disabled={tableauStep >= tw.steps.length - 1}
        aria-label="Next tableau step"
        onclick={() => {
          tableauStep = Math.min(tw.steps.length - 1, tableauStep + 1);
        }}>Next →</button>
    </div>
  </div>
  <p class="muted small tableau-lede">{tw.initial_narrative}</p>
  {#if st}
    <p class="tableau-narrative">{st.narrative}</p>
  {/if}
  {#if st}
    <div class="table-wrap">
      <table class="tableau">
        <colgroup>
          <col class="tableau-col-basis" />
        </colgroup>
        <thead>
          <tr>
            <th scope="col" class="tableau-corner">Basis</th>
            {#each st.column_labels as lab}
              <th scope="col" class="tableau-num-head">{lab}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each st.tableau as row, rowIdx}
            <tr>
              <th scope="row" class="tableau-row-label"
                >{tableauRowLabel(rowIdx, st.tableau.length, st.basis_labels)}</th>
              {#each row as cell}
                <td class="tableau-num">{formatTableauCell(cell)}</td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    {#if st?.ratios?.length}
      {@const ratioNums = st.ratios.filter((r) => r != null && Number.isFinite(r))}
      {#if ratioNums.length > 0}
        {@const dualRatios = isDualRatioNarrative(st.narrative)}
        {@const primalByRow = !dualRatios && st.ratios.length === st.basis_labels.length}
        {@const enteringName =
          st.entering_col != null &&
          st.entering_col >= 0 &&
          st.entering_col < st.column_labels.length &&
          st.column_labels[st.entering_col] !== "RHS"
            ? st.column_labels[st.entering_col]
            : null}
        <div class="tableau-ratios" role="region" aria-label="Ratio test values for this step">
          <p class="tableau-ratios-lede">
            {#if dualRatios}
              Dual ratio test · one value per tableau column for this pivot
            {:else if enteringName}
              Primal minimum ratio test · use the <strong>{enteringName}</strong> column with each
              <strong>constraint</strong> row (ignore the bottom z-row here)
            {:else}
              Primal minimum ratio test · one ratio per constraint row
            {/if}
          </p>
          {#if primalByRow}
            <ul class="tableau-ratios-list">
              {#each st.ratios as r, i (i)}
                <li>
                  <span class="tableau-ratios-k">Row {i + 1} ({st.basis_labels[i]}):</span>
                  <code class="tableau-ratios-v">{r == null || !Number.isFinite(r) ? "—" : formatRatio(r)}</code>
                </li>
              {/each}
            </ul>
            <p class="muted small tableau-ratios-hint hint-on">
              For row <em>i</em> in the basis list above: divide that row&rsquo;s <strong>RHS</strong> by the number in
              the <strong>{enteringName ?? "entering"}</strong> column on the same row. If that entry is
              <strong>greater than 0</strong>, you get a ratio; if it is <strong>zero or negative</strong>, the
              ratio is <strong>–</strong> (that row does not cap how far you can increase the entering variable).
              The <strong>smallest</strong> positive ratio is the winner; its row is where the <strong>leaving</strong>
              basic variable is chosen.
            </p>
          {:else}
            <ul class="tableau-ratios-list tableau-ratios-cols">
              {#each st.ratios as r, j (j)}
                {#if j < st.column_labels.length - 1 && st.column_labels[j] !== "RHS"}
                  <li>
                    <span class="tableau-ratios-k">{st.column_labels[j]}:</span>
                    <code class="tableau-ratios-v">{r == null || !Number.isFinite(r) ? "—" : formatRatio(r)}</code>
                  </li>
                {/if}
              {/each}
            </ul>
            <p class="muted small tableau-ratios-hint hint-on">
              {#if dualRatios}
                One entry per column header (not RHS). <strong>–</strong> means that column is not eligible for the
                dual ratio rule on this pivot. The smallest finite eligible ratio picks the <strong>entering</strong>
                variable.
              {:else}
                <strong>–</strong> marks columns that do not get a ratio on this step.
              {/if}
            </p>
          {/if}
        </div>
      {/if}
    {/if}
    <p class="muted small tableau-basis hint-on">
      Each constraint row shows its basic variable in the first column; the bottom row is the z-row (objective,
      maximize slack form).
    </p>
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
  .tag {
    font-family: var(--font-sans);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.2rem 0.45rem;
    border-radius: 999px;
    border: 1px solid var(--color-border-strong);
    color: var(--color-text-muted);
    background: var(--color-bg-deep);
  }
  .muted {
    color: var(--color-text-muted);
  }
  .small {
    font-size: 0.875rem;
    line-height: 1.5;
  }
  .panel {
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 1.1rem 1.15rem 1.2rem;
    box-shadow: var(--shadow);
  }
  .table-wrap {
    overflow-x: auto;
    overflow-y: visible;
    -webkit-overflow-scrolling: touch;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    background: var(--color-surface);
    margin-top: 0.85rem;
  }
  table.tableau {
    border-collapse: collapse;
    table-layout: auto;
    width: max-content;
    min-width: 100%;
    max-width: none;
    font-size: 0.95rem;
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums lining-nums;
  }
  col.tableau-col-basis {
    width: auto;
    min-width: 4.5rem;
  }
  table.tableau th,
  table.tableau td {
    border-bottom: 1px solid var(--color-border);
    padding: 0.5rem 0.65rem;
    vertical-align: middle;
  }
  table.tableau .tableau-corner,
  table.tableau .tableau-row-label {
    text-align: left;
    font-weight: 600;
    color: var(--color-text-muted);
    white-space: nowrap;
  }
  table.tableau tbody .tableau-row-label {
    font-weight: 600;
    color: var(--color-text);
    background: var(--color-bg-deep);
    border-right: 1px solid var(--color-border-strong);
  }
  table.tableau .tableau-num-head,
  table.tableau .tableau-num {
    text-align: right;
    white-space: nowrap;
    min-width: 3.25rem;
  }
  table.tableau tbody tr:nth-child(even) .tableau-num {
    background: color-mix(in srgb, var(--color-bg) 55%, transparent);
  }
  table.tableau thead th {
    background: var(--color-bg-deep);
    color: var(--color-text);
    font-weight: 600;
    border-bottom-color: var(--color-border-strong);
  }
  table.tableau thead .tableau-corner {
    border-right: 1px solid var(--color-border-strong);
  }
  .tableau-panel-bottom {
    margin-top: 1rem;
  }
  .tableau-head {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 0.75rem 1.25rem;
    margin-bottom: 0.35rem;
  }
  .tableau-title {
    margin: 0;
    flex: 1 1 12rem;
  }
  .tableau-step-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.65rem 1rem;
    padding: 0.45rem 0.65rem;
    border-radius: var(--radius-sm);
    background: var(--color-bg-deep);
    border: 1px solid var(--color-border);
  }
  .tableau-step-btn {
    font-family: var(--font-sans);
    background: transparent;
    color: var(--color-text);
    border: 1px solid var(--color-border-strong);
    box-shadow: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    padding: 0.55rem 1.15rem !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    min-width: 6.5rem;
  }
  .tableau-step-btn:hover:not(:disabled) {
    background: var(--color-bg-deep);
  }
  .tableau-step-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .tableau-step-label {
    font-size: 0.95rem;
    color: var(--color-text);
    min-width: 8.5rem;
    text-align: center;
  }
  .tableau-lede {
    margin: 0.5rem 0 0;
    line-height: 1.45;
    max-width: 60rem;
  }
  .tableau-narrative {
    margin: 0.65rem 0 0;
    line-height: 1.5;
    font-size: 0.95rem;
    max-width: 60rem;
  }
  .tableau-ratios {
    margin: 0.5rem 0 0;
    padding: 0.55rem 0.7rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
    background: color-mix(in srgb, var(--color-bg-deep) 65%, var(--color-surface-raised));
    max-width: 52rem;
  }
  .tableau-ratios-lede {
    margin: 0 0 0.4rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--color-text-muted);
  }
  .tableau-ratios-list {
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.28rem 1rem;
    font-size: 0.86rem;
  }
  @media (min-width: 640px) {
    .tableau-ratios-list.tableau-ratios-cols {
      flex-flow: row wrap;
    }
  }
  .tableau-ratios-list li {
    display: flex;
    align-items: baseline;
    gap: 0.35rem;
    min-width: 0;
  }
  .tableau-ratios-k {
    color: var(--color-text-muted);
    font-weight: 500;
    flex: 0 0 auto;
  }
  .tableau-ratios-v {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-size: 0.84rem;
  }
  .tableau-ratios-hint {
    margin: 0.45rem 0 0;
    line-height: 1.45;
  }
  .tableau-basis {
    margin: 0.65rem 0 0;
  }
  .tableau-sense {
    font-weight: 500;
  }
  .tableau-compact table.tableau {
    font-size: 0.82rem;
  }
  .tableau-compact table.tableau th,
  .tableau-compact table.tableau td {
    padding: 0.38rem 0.45rem;
  }
  .tableau-compact .tableau-step-btn {
    padding: 0.45rem 0.85rem !important;
    font-size: 0.88rem !important;
    min-width: 5.5rem;
  }
  .tableau-compact .tableau-step-label {
    font-size: 0.88rem;
  }
</style>
