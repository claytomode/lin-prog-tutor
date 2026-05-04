<script lang="ts">
  let { source }: { source: string } = $props();
</script>

<aside class="lp-print-sheet" aria-label="Printable worksheet">
  <h2 class="print-sheet-title">Linear program (worksheet)</h2>
  <pre class="print-problem">{source}</pre>
  <div class="print-workspace">
    <p class="print-workspace-label">Workspace</p>
  </div>
</aside>
