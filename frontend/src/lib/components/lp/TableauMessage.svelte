<script lang="ts">
  let { message }: { message: string } = $props();
</script>

<section class="panel tableau-panel tableau-panel-bottom">
  <h2 class="panel-title">Tableau</h2>
  <p class="muted">{message}</p>
</section>

<style>
  .panel-title {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0 0 0.85rem;
    color: var(--color-text);
  }
  .muted {
    color: var(--color-text-muted);
  }
  .panel {
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 1.1rem 1.15rem 1.2rem;
    box-shadow: var(--shadow);
  }
  .tableau-panel-bottom {
    margin-top: 1rem;
  }
</style>
