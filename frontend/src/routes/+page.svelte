<script lang="ts">
  import { page } from "$app/state";
  import { onMount, tick } from "svelte";
  import FeasiblePlotPanel from "$lib/components/lp/FeasiblePlotPanel.svelte";
  import GrobnerTrace from "$lib/components/lp/GrobnerTrace.svelte";
  import GraphicalTutor from "$lib/components/lp/GraphicalTutor.svelte";
  import HeroSection from "$lib/components/lp/HeroSection.svelte";
  import ModelingNotes from "$lib/components/lp/ModelingNotes.svelte";
  import ModelPanel from "$lib/components/lp/ModelPanel.svelte";
  import PrintWorksheet from "$lib/components/lp/PrintWorksheet.svelte";
  import ResultsSkeleton from "$lib/components/lp/ResultsSkeleton.svelte";
  import SolutionPanel from "$lib/components/lp/SolutionPanel.svelte";
  import TableauMessage from "$lib/components/lp/TableauMessage.svelte";
  import TableauWalkthrough from "$lib/components/lp/TableauWalkthrough.svelte";
  import { humanizeApiError } from "$lib/lp/api-errors.js";
  import { defaultSource, PRESET_STORAGE_KEY, presetFlags } from "$lib/lp/constants.js";
  import { docExamples } from "$lib/lp/doc-examples.js";
  import type { StudyPreset } from "$lib/lp/constants.js";
  import { isPolyhedron3d } from "$lib/lp/feasible.js";
  import type {
    AnalyzeResponse,
    MipSolveMethod,
    ProblemClass,
    TableauMode,
    VariableDomain,
  } from "$lib/lp/types.js";

  let source = $state(defaultSource);
  let loading = $state(false);
  let err = $state<string | null>(null);
  let data = $state<AnalyzeResponse | null>(null);
  let activeStep = $state(0);
  let tableauStep = $state(0);
  let tableauMode = $state<TableauMode>("auto");
  let useBlandsRule = $state(false);
  let bigMText = $state("");
  let studyPreset = $state<StudyPreset>("default");
  let problemClass = $state<ProblemClass>("auto");
  let mipMethod = $state<MipSolveMethod>("scipy_milp");
  let variableDomains = $state<Record<string, VariableDomain>>({});
  let domainVariableNames = $state<string[]>([]);
  /** Source text used when `domainVariableNames` / `variableDomains` were last filled from the API. */
  let domainSyncSource = $state("");
  let presetHydrated = $state(false);
  let solutionHeadingEl = $state<HTMLHeadingElement | null>(null);
  let lastAppliedQuery = $state<string | null>(null);

  const showHints = $derived(presetFlags(studyPreset).hintsDefault);
  const skipPlot3d = $derived(presetFlags(studyPreset).skipPlot3d);
  const compactTableau = $derived(presetFlags(studyPreset).compactTableau);

  onMount(() => {
    const raw = localStorage.getItem(PRESET_STORAGE_KEY);
    if (raw === "classroom" || raw === "self-study" || raw === "default") {
      studyPreset = raw;
    }
    presetHydrated = true;
  });

  $effect(() => {
    const query = page.url.search;
    if (query === lastAppliedQuery) return;
    const params = page.url.searchParams;
    const sourceParam = params.get("source");
    const example = params.get("example");
    if (sourceParam && sourceParam.trim().length > 0) {
      source = sourceParam;
      lastAppliedQuery = query;
      return;
    }
    if (example && docExamples[example]) {
      source = docExamples[example];
      lastAppliedQuery = query;
      return;
    }
    if (!query) {
      lastAppliedQuery = query;
    }
  });

  $effect(() => {
    if (typeof localStorage === "undefined" || !presetHydrated) return;
    localStorage.setItem(PRESET_STORAGE_KEY, studyPreset);
  });

  function parseBigM(): number | null {
    const t = bigMText.trim();
    if (t === "") return null;
    const n = Number(t);
    return Number.isFinite(n) ? n : null;
  }

  async function analyze() {
    loading = true;
    err = null;
    data = null;
    activeStep = 0;
    tableauStep = 0;
    try {
      // Stale UI domains from a *previous* model would still be sent and override the DSL
      // (`variables x integer, ...`). Only reuse them when the source matches the last sync.
      if (domainSyncSource !== "" && source !== domainSyncSource) {
        domainVariableNames = [];
        variableDomains = {};
      }

      const big_m_value = parseBigM();
      const payload: Record<string, unknown> = {
        source,
        problem_class: problemClass,
        mip_method: mipMethod,
        tableau_mode: tableauMode,
        use_blands_rule: useBlandsRule,
        big_m_value,
      };
      if (domainVariableNames.length > 0 && source === domainSyncSource) {
        payload.variable_domains = Object.fromEntries(
          domainVariableNames.map((v) => [v, variableDomains[v] ?? "continuous"]),
        );
      }
      const res = await fetch("/api/lp/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      let raw: unknown;
      try {
        raw = await res.json();
      } catch {
        err = `Could not read response (HTTP ${res.status} ${res.statusText}). Is the API running (dev proxy → port 8010)?`;
        return;
      }
      if (!res.ok) {
        const j = raw as { error?: string; detail?: unknown; error_code?: string; error_hint?: string };
        const d = j.detail;
        const message =
          typeof j.error === "string"
            ? j.error
            : typeof d === "string"
              ? d
              : `Request failed (HTTP ${res.status})`;
        err = humanizeApiError({
          code: j.error_code ?? null,
          hint: j.error_hint ?? null,
          message,
        });
        return;
      }
      const parsed = raw as AnalyzeResponse;
      const json: AnalyzeResponse = {
        ...parsed,
        modeling_notes: parsed.modeling_notes ?? [],
        tableau_verified: parsed.tableau_verified ?? null,
        tableau_verify_message: parsed.tableau_verify_message ?? null,
      };
      if (!json.ok) {
        err = humanizeApiError({
          code: json.error_code ?? null,
          hint: json.error_hint ?? null,
          message: json.error ?? "Request failed",
        });
        return;
      }
      data = json;
      if (json.problem) {
        domainVariableNames = json.problem.variables;
        const dom = json.problem.variable_domains ?? {};
        variableDomains = Object.fromEntries(
          json.problem.variables.map((v) => [v, dom[v] ?? "continuous"]),
        ) as Record<string, VariableDomain>;
        domainSyncSource = source;
      }
      await tick();
      solutionHeadingEl?.focus();
    } catch (e) {
      err = humanizeApiError({ message: e instanceof Error ? e.message : String(e) });
    } finally {
      loading = false;
    }
  }

  function printWorksheet() {
    window.print();
  }
</script>

<div
  class="lp-page"
  data-hints={showHints ? "on" : "off"}
  aria-busy={loading ? true : undefined}
>
  <div class="lp-screen">
    <HeroSection />

    <div class="grid">
      <ModelPanel
        bind:source
        {loading}
        {err}
        bind:tableauMode
        bind:useBlandsRule
        bind:bigMText
        bind:studyPreset
        bind:problemClass
        bind:mipMethod
        bind:variableDomains
        bind:domainVariableNames
        onAnalyze={analyze}
        onResetExample={() => {
          source = defaultSource;
          variableDomains = {};
          domainVariableNames = [];
          domainSyncSource = "";
        }}
        onPrintWorksheet={printWorksheet}
      />

      <FeasiblePlotPanel {data} {loading} {activeStep} {skipPlot3d} />
    </div>

    <div class="lp-below-grid">
      {#if data}
        <SolutionPanel bind:solutionHeadingEl {data} />

        {#if (data.modeling_notes?.length ?? 0) > 0}
          <ModelingNotes notes={data.modeling_notes ?? []} />
        {/if}

        {#if !(isPolyhedron3d(data) && skipPlot3d) && !data.problem?.is_mip}
          <GraphicalTutor steps={data.tutor_steps} bind:activeStep />
        {/if}

        {#if data.tableau_walkthrough && !data.problem?.is_mip}
          <TableauWalkthrough
            walkthrough={data.tableau_walkthrough}
            {compactTableau}
            bind:tableauStep
          />
        {:else if data.tableau_message}
          <TableauMessage message={data.tableau_message} />
        {/if}

        {#if data.grobner_walkthrough}
          <GrobnerTrace walkthrough={data.grobner_walkthrough} />
        {/if}
      {:else}
        <ResultsSkeleton {loading} />
      {/if}
    </div>
  </div>

  <PrintWorksheet {source} />
</div>

<style>
  .lp-page[data-hints="off"] :global(.hint-on) {
    display: none !important;
  }
  .grid {
    display: grid;
    gap: 1.1rem;
    margin-top: 0.25rem;
  }
  @media (min-width: 900px) {
    .grid {
      grid-template-columns: minmax(0, 1fr) minmax(0, 1.12fr);
      align-items: start;
    }
  }
  .lp-below-grid {
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    margin-top: 1.1rem;
  }
</style>
