<script lang="ts">
  import "katex/dist/katex.min.css";
  import { renderMarkdownToHtml } from "$lib/docs/markdown.js";
  import type { components } from "$lib/api/openapi";

  type GW = components["schemas"]["GrobnerWalkthrough"];

  let { walkthrough }: { walkthrough: GW } = $props();

  /** Markdown + KaTeX (marked-katex); pass strings that may include `$...$`. */
  function md(s: string | null | undefined): string {
    if (s == null || s === "") return "";
    return renderMarkdownToHtml(s);
  }

  /** Backend stores LaTeX fragments without delimiters for remainder / basis rows. */
  function texBlock(s: string | null | undefined): string {
    if (s == null || s === "") return "";
    const t = s.trim();
    if (t.includes("$")) return renderMarkdownToHtml(t);
    // Inline \\displaystyle avoids .katex-display (centered blocks + overflow scroll UI in narrow panels).
    return renderMarkdownToHtml(`$\\displaystyle ${t}$`);
  }
</script>

<section class="panel grobner" aria-label="Gröbner basis walkthrough">
  <h2 class="panel-title">Gröbner / toric trace</h2>
  <div class="grobner-md intro">{@html md(walkthrough.initial_narrative)}</div>
  <p class="small outcome">
    Outcome: <code>{walkthrough.outcome}</code>
  </p>
  {#if walkthrough.optimality_note}
    <div class="grobner-md note">{@html md(walkthrough.optimality_note)}</div>
  {/if}
  {#if walkthrough.agrees_with_scipy_mip != null}
    <p class="small agree">
      Matches SciPy MILP on original variables:
      <code>{walkthrough.agrees_with_scipy_mip ? "yes" : "no"}</code>
    </p>
  {/if}
  {#if walkthrough.point_from_normal_form && Object.keys(walkthrough.point_from_normal_form).length > 0}
    <p class="small">
      NF exponent vector (incl. slacks):
      <code>{JSON.stringify(walkthrough.point_from_normal_form)}</code>
    </p>
  {/if}
  {#if walkthrough.remainder_str}
    <div class="remainder-block small">
      <div class="remainder-label">Remainder</div>
      <div class="remainder-math grobner-md">{@html texBlock(walkthrough.remainder_str)}</div>
    </div>
  {/if}
  {#if (walkthrough.grobner_basis_strs?.length ?? 0) > 0}
    <details class="gb-details">
      <summary>Gröbner basis (truncated)</summary>
      <ul class="gb-list grobner-md">
        {#each walkthrough.grobner_basis_strs ?? [] as g (g)}
          <li class="gb-li"><span class="gb-math">{@html texBlock(g)}</span></li>
        {/each}
      </ul>
    </details>
  {/if}
  {#if (walkthrough.steps?.length ?? 0) > 0}
    <ol class="steps">
      {#each walkthrough.steps ?? [] as st (st.index + ":" + st.title)}
        <li>
          <div class="step-title grobner-md">{@html md(st.title)}</div>
          <div class="step-detail grobner-md">{@html md(st.detail)}</div>
        </li>
      {/each}
    </ol>
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
  .intro {
    margin: 0 0 0.65rem;
    line-height: 1.55;
  }
  .outcome,
  .agree,
  .note {
    margin: 0.35rem 0;
  }
  .remainder-block {
    margin: 0.45rem 0 0.55rem;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.2rem;
  }
  .remainder-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--color-text-muted);
    letter-spacing: 0.02em;
  }
  .remainder-math {
    width: 100%;
    padding: 0.35rem 0 0;
    border-top: 1px solid var(--color-border);
  }
  .gb-details {
    margin: 0.75rem 0;
  }
  .gb-list {
    margin: 0.45rem 0 0;
    padding-left: 0;
    font-size: 0.9rem;
    list-style: none;
  }
  .gb-li {
    margin: 0.4rem 0;
    padding-left: 0.85rem;
    border-left: 3px solid var(--color-border);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.15rem;
  }
  .gb-math {
    line-height: 1.45;
  }
  .steps {
    margin: 0.85rem 0 0;
    padding-left: 1.25rem;
    line-height: 1.55;
  }
  .steps li {
    margin: 0.55rem 0;
  }
  .step-title {
    font-weight: 600;
    margin-bottom: 0.2rem;
    color: var(--color-text);
  }
  .step-detail {
    margin-top: 0.15rem;
    font-size: 0.92rem;
    color: var(--color-text-muted);
  }

  .grobner-md :global(p) {
    margin: 0.35rem 0;
    text-align: left;
  }
  .grobner-md :global(p:first-child) {
    margin-top: 0;
  }
  .grobner-md :global(p:last-child) {
    margin-bottom: 0;
  }
  .grobner-md :global(ul),
  .grobner-md :global(ol) {
    margin: 0.35rem 0;
    padding-left: 1.25rem;
  }
  .grobner-md :global(.katex) {
    font-size: 1.02em;
  }
  /* Tame KaTeX in tight panels: no horizontal scroll chrome, left-aligned if display math appears. */
  .grobner-md :global(.katex-display) {
    margin: 0.35rem 0;
    overflow-x: visible;
    overflow-y: visible;
    text-align: left;
    max-width: 100%;
  }
  .grobner-md :global(.katex-display > .katex) {
    margin: 0 auto 0 0;
  }
</style>
