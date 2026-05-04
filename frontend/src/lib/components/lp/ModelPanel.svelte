<script lang="ts">
  import type { StudyPreset } from "$lib/lp/constants.js";
  import type { TableauMode } from "$lib/lp/types.js";

  let {
    source = $bindable(),
    loading,
    err,
    tableauMode = $bindable<TableauMode>(),
    useBlandsRule = $bindable(false),
    bigMText = $bindable(""),
    studyPreset = $bindable<StudyPreset>("default"),
    onAnalyze,
    onResetExample,
    onPrintWorksheet,
  }: {
    source: string;
    loading: boolean;
    err: string | null;
    tableauMode: TableauMode;
    useBlandsRule: boolean;
    bigMText: string;
    studyPreset: StudyPreset;
    onAnalyze: () => void;
    onResetExample: () => void;
    onPrintWorksheet: () => void;
  } = $props();
</script>

<section class="panel">
  <h2 class="panel-title">Model</h2>
  <label for="src">Source</label>
  <textarea id="src" bind:value={source} rows="14" spellcheck="false"></textarea>
  <details class="solver-details">
    <summary>Tableau &amp; solver options</summary>
    <div class="solver-details-body">
      <label for="tab-mode">Tableau mode</label>
      <select id="tab-mode" bind:value={tableauMode}>
        <option value="auto">Auto</option>
        <option value="primal">Primal (two-phase)</option>
        <option value="dual">Dual simplex</option>
        <option value="big_m">Big-M</option>
      </select>
      <label class="check-row">
        <input type="checkbox" bind:checked={useBlandsRule} />
        Use Bland&rsquo;s rule (tie-breaking)
      </label>
      {#if tableauMode === "big_m"}
        <label for="big-m">Big M (optional)</label>
        <input
          id="big-m"
          class="big-m-input"
          type="text"
          inputmode="decimal"
          bind:value={bigMText}
          placeholder="Default from model scale"
          autocomplete="off"
        />
      {/if}
    </div>
  </details>
  <div class="preset-row">
    <label for="preset">Session preset</label>
    <select id="preset" bind:value={studyPreset}>
      <option value="default">Default</option>
      <option value="classroom">Classroom</option>
      <option value="self-study">Self-study</option>
    </select>
    <span class="muted small preset-hint"
      >Classroom: compact tableau, skip 3D plot/tutor, fewer on-screen hints.</span
    >
  </div>
  <div class="row">
    <button
      type="button"
      class="btn-analyze"
      onclick={onAnalyze}
      disabled={loading}
      aria-busy={loading ? true : undefined}
    >
      <span class="btn-analyze-left" aria-hidden="true">
        {#if loading}
          <span class="spinner spinner--btn"></span>
        {:else}
          <span class="btn-analyze-slot"></span>
        {/if}
      </span>
      <span class="btn-analyze-label">Analyze</span>
      <span class="btn-analyze-right" aria-hidden="true"><span class="btn-analyze-slot"></span></span>
    </button>
    <button type="button" class="ghost" onclick={onResetExample}>Reset example</button>
    <button type="button" class="ghost" onclick={onPrintWorksheet}>Print worksheet</button>
  </div>
  {#if err}
    <p class="error">{err}</p>
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
  .error {
    margin: 0.75rem 0 0;
    padding: 0.65rem 0.75rem;
    border-radius: var(--radius-sm);
    background: var(--color-danger-bg);
    color: var(--color-danger);
    border: 1px solid #f0c4c4;
    font-size: 0.9rem;
  }
  .panel {
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 1.1rem 1.15rem 1.2rem;
    box-shadow: var(--shadow);
  }
  label {
    display: block;
    margin: 0 0 0.4rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--color-text-muted);
  }
  textarea {
    width: 100%;
    box-sizing: border-box;
    font-family: var(--font-mono);
    font-size: 0.84rem;
    line-height: 1.5;
    background: var(--color-surface);
    color: var(--color-text);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-sm);
    padding: 0.75rem 0.85rem;
    resize: vertical;
    box-shadow: var(--shadow-inset);
  }
  textarea:focus {
    outline: 2px solid color-mix(in srgb, var(--color-accent) 45%, transparent);
    outline-offset: 1px;
    border-color: var(--color-accent);
  }
  .row {
    display: flex;
    gap: 0.55rem;
    align-items: center;
    margin-top: 0.85rem;
    flex-wrap: wrap;
  }
  .btn-analyze {
    display: inline-grid;
    grid-template-columns: 1.15rem auto 1.15rem;
    align-items: center;
    justify-items: center;
    column-gap: 0.35rem;
  }
  .btn-analyze-left,
  .btn-analyze-right {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.15rem;
    height: 1.15rem;
  }
  .btn-analyze-left {
    grid-column: 1;
  }
  .btn-analyze-label {
    grid-column: 2;
  }
  .btn-analyze-right {
    grid-column: 3;
  }
  .btn-analyze-slot {
    display: block;
    width: 1.05rem;
    height: 1.05rem;
    flex-shrink: 0;
  }
  .spinner.spinner--btn {
    width: 1.05rem;
    height: 1.05rem;
    border-width: 2px;
  }
  button {
    font-family: var(--font-sans);
    background: var(--color-accent);
    color: #fdfcfa;
    border: 1px solid color-mix(in srgb, var(--color-accent) 88%, #000);
    border-radius: var(--radius-sm);
    padding: 0.55rem 1.05rem;
    font-weight: 600;
    font-size: 0.92rem;
    letter-spacing: -0.01em;
    cursor: pointer;
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.12) inset;
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
  }
  button:focus {
    outline: none;
  }
  button:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }
  button:hover:not(:disabled) {
    background: var(--color-accent-hover);
  }
  button:active:not(:disabled) {
    transform: none;
    background: var(--color-accent-hover);
  }
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  button.ghost {
    background: transparent;
    color: var(--color-text);
    border: 1px solid var(--color-border-strong);
    box-shadow: none;
  }
  button.ghost:hover:not(:disabled) {
    background: var(--color-bg-deep);
    border-color: var(--color-text-faint);
  }
  button.ghost:active:not(:disabled) {
    background: var(--color-bg-deep);
    border-color: var(--color-text-faint);
  }
  .solver-details {
    margin-top: 0.75rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: 0.35rem 0.65rem;
    background: var(--color-surface);
  }
  .solver-details summary {
    cursor: pointer;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--color-text-muted);
    user-select: none;
  }
  .solver-details-body {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    margin-top: 0.65rem;
    padding-top: 0.55rem;
    border-top: 1px solid var(--color-border);
  }
  .solver-details-body select,
  .big-m-input {
    font-family: var(--font-sans);
    font-size: 0.88rem;
    padding: 0.35rem 0.45rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border-strong);
    background: var(--color-surface-raised);
    color: var(--color-text);
    max-width: 16rem;
  }
  .check-row {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.86rem;
    color: var(--color-text);
    font-weight: 500;
  }
  .preset-row {
    margin-top: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }
  .preset-hint {
    max-width: 36rem;
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
</style>
