<script lang="ts">
  let { notes }: { notes: string[] } = $props();
</script>

<section class="panel modeling-notes">
  <h2 class="panel-title">Modeling notes</h2>
  <ul class="modeling-notes-list">
    {#each notes as note, i (i)}
      <li>{note}</li>
    {/each}
  </ul>
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
  .modeling-notes-list {
    margin: 0;
    padding-left: 1.15rem;
    color: var(--color-text);
    font-size: 0.92rem;
    line-height: 1.55;
  }
  .modeling-notes-list li {
    margin: 0.25rem 0;
  }
</style>
