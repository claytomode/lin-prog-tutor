<script lang="ts">
  import type { TutorStep } from "$lib/lp/types.js";

  let {
    steps,
    activeStep = $bindable(0),
  }: {
    steps: TutorStep[];
    activeStep: number;
  } = $props();
</script>

<div class="grid grid-tutor-row">
  <section class="panel panel-tutor">
    <h2 class="panel-title">Graphical tutor</h2>
    <ol class="steps">
      {#each steps as step, i (step.id)}
        <li>
          <button
            type="button"
            class:sel={i === activeStep}
            onclick={() => {
              activeStep = i;
            }}
          >
            <strong>{step.title}</strong>
            <span class="detail">{step.detail}</span>
          </button>
        </li>
      {/each}
    </ol>
  </section>
</div>

<style>
  .panel-title {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0 0 0.85rem;
    color: var(--color-text);
  }
  .grid {
    display: grid;
    gap: 1.1rem;
    margin-top: 0.25rem;
  }
  .grid-tutor-row {
    grid-template-columns: minmax(0, 1fr);
  }
  .panel-tutor {
    min-height: 0;
    width: 100%;
    max-width: none;
  }
  .panel {
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 1.1rem 1.15rem 1.2rem;
    box-shadow: var(--shadow);
  }
  ol.steps {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }
  ol.steps li button {
    width: 100%;
    text-align: left;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    color: var(--color-text);
    font-weight: 500;
    box-shadow: none;
    padding: 0.65rem 0.75rem;
    font-family: var(--font-sans);
    border-radius: var(--radius-sm);
    cursor: pointer;
  }
  ol.steps li button:hover {
    border-color: var(--color-border-strong);
    background: color-mix(in srgb, var(--color-surface-raised) 70%, var(--color-bg));
  }
  ol.steps li button.sel {
    border-color: var(--color-accent);
    box-shadow: 0 0 0 1px var(--color-accent) inset;
    background: color-mix(in srgb, var(--color-surface-raised) 55%, var(--color-bg));
  }
  ol.steps li button:active:not(:disabled) {
    border-color: var(--color-border-strong);
    background: color-mix(in srgb, var(--color-surface-raised) 70%, var(--color-bg));
    box-shadow: none;
  }
  ol.steps li button.sel:active:not(:disabled) {
    border-color: var(--color-accent);
    box-shadow: 0 0 0 1px var(--color-accent) inset;
    background: color-mix(in srgb, var(--color-surface-raised) 55%, var(--color-bg));
  }
  .detail {
    display: block;
    font-weight: 450;
    color: var(--color-text-muted);
    margin-top: 0.25rem;
    font-size: 0.84rem;
    line-height: 1.45;
  }
</style>
