<script lang="ts">
  import { onMount } from 'svelte';
  import {
    SENSITIVITY_PARAMS,
    baseIndex,
    curvePath,
    decadeTicks,
    decodeSensitivity,
    linearTicks,
    scaleX,
    scaleY,
    valueText,
    type DecodedSensitivity,
    type Frame,
  } from '../../lib/sensitivity';

  // The sensitivity check of Chapter 13: the CoC4 starting model with one
  // parameter changed at a time. X-Ray Calc computed every curve in advance
  // (scripts/figures/ch13_engine_data.py); this component fetches them,
  // and src/lib/sensitivity.ts decodes and draws them.

  const uid = $props.id();
  const DATA_URL = `${import.meta.env.BASE_URL.replace(/\/$/, '')}/data/ch13-sensitivity.json`;

  let status = $state<'loading' | 'ready' | 'error'>('loading');
  let data = $state.raw<DecodedSensitivity | null>(null);
  let paramKey = $state(SENSITIVITY_PARAMS[0].key);
  let stepIdx = $state(baseIndex(SENSITIVITY_PARAMS[0].key));

  onMount(async () => {
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = decodeSensitivity(await res.json());
      status = 'ready';
    } catch (e) {
      console.error('SensitivityCheck: the curves could not be loaded.', e);
      status = 'error';
    }
  });

  function chooseParam(key: string) {
    paramKey = key;
    stepIdx = baseIndex(key);
  }

  let param = $derived(data?.params.find((p) => p.key === paramKey) ?? null);
  let step = $derived(param ? param.steps[Math.min(stepIdx, param.steps.length - 1)] : null);
  let readout = $derived(
    param && step
      ? valueText(param.label, param.unit, step.label) + (step.isBase ? ' (starting model)' : '')
      : '',
  );
  let sliderMax = $derived(param ? param.steps.length - 1 : 4);

  // ---- the chart ----
  // The SVG takes the width of its box, so the labels keep their size on a phone.
  let boxWidth = $state(560);
  let W = $derived(Math.max(260, Math.round(boxWidth)));
  let H = $derived(Math.max(240, Math.round(W * 0.6)));
  const M = { left: 56, right: 12, top: 10, bottom: 40 };
  let frame = $derived<Frame>({
    x0: 0,
    x1: 14,
    y0: -8,
    y1: 0,
    left: M.left,
    right: W - M.right,
    bottom: H - M.bottom,
    top: M.top,
  });
  const xTicks = linearTicks(0, 14, 2);
  const yTicks = decadeTicks(-8, 0);

  let measuredPath = $derived(data ? curvePath(data.measuredX, data.measured, frame) : '');
  let basePath = $derived(data ? curvePath(data.modelX, data.base, frame) : '');
  let variantPath = $derived(data && step && !step.isBase ? curvePath(data.modelX, step.y, frame) : '');
</script>

<div class="widget sensitivity-check">
  <p class="hint">
    Choose one parameter of the starting model, then move the slider to change it. The dashed line
    is the starting model. The solid line is the model with the changed parameter. The gray line
    behind them is the measured curve CoC4. X-Ray Calc computed each curve in advance, so the slider
    moves in fixed steps.
  </p>

  <fieldset class="params" disabled={status !== 'ready'}>
    <legend>Parameter to change</legend>
    {#each SENSITIVITY_PARAMS as p (p.key)}
      <label>
        <input
          type="radio"
          name={`${uid}-param`}
          value={p.key}
          checked={paramKey === p.key}
          onchange={() => chooseParam(p.key)}
        />
        {p.label}
      </label>
    {/each}
  </fieldset>

  <div class="step">
    <label for={`${uid}-step`}>Value</label>
    <input
      id={`${uid}-step`}
      type="range"
      min="0"
      max={sliderMax}
      step="1"
      bind:value={stepIdx}
      disabled={status !== 'ready'}
      aria-valuetext={readout || undefined}
    />
  </div>

  <p class="readout" aria-live="polite">
    {#if status === 'ready'}
      {readout}
    {:else if status === 'loading'}
      Loading the precomputed curves…
    {:else}
      The curves could not be loaded. Reload the page to try again.
    {/if}
  </p>

  <div class="chart" bind:clientWidth={boxWidth}>
    <svg
      width={W}
      height={H}
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label="Reflectivity R on a logarithmic axis against 2θ from 0° to 14°: the measured curve, the starting model and the changed model"
    >
      <defs>
        <clipPath id={`${uid}-clip`}>
          <rect x={frame.left} y={frame.top} width={frame.right - frame.left} height={frame.bottom - frame.top} />
        </clipPath>
      </defs>

      {#each yTicks as t (t.exp)}
        {@const y = scaleY(frame, t.exp)}
        <line class="grid" x1={frame.left} x2={frame.right} y1={y} y2={y} />
        <text class="tick" x={frame.left - 6} y={y} text-anchor="end" dominant-baseline="middle">{t.label}</text>
      {/each}
      {#each xTicks as t (t)}
        {@const x = scaleX(frame, t)}
        <line class="grid" x1={x} x2={x} y1={frame.top} y2={frame.bottom} />
        <text class="tick" x={x} y={frame.bottom + 16} text-anchor="middle">{t}</text>
      {/each}
      <rect
        class="axes"
        x={frame.left}
        y={frame.top}
        width={frame.right - frame.left}
        height={frame.bottom - frame.top}
      />
      <text class="title" x={(frame.left + frame.right) / 2} y={H - 6} text-anchor="middle">2θ (°)</text>
      <text class="title" x={10} y={(frame.top + frame.bottom) / 2} text-anchor="middle" dominant-baseline="middle">R</text>

      <g clip-path={`url(#${uid}-clip)`}>
        {#if measuredPath}<path class="measured" d={measuredPath} />{/if}
        {#if basePath}<path class="base" d={basePath} />{/if}
        {#if variantPath}<path class="variant" d={variantPath} />{/if}
      </g>

      {#if status !== 'ready'}
        <text class="status" x={(frame.left + frame.right) / 2} y={(frame.top + frame.bottom) / 2} text-anchor="middle">
          {status === 'loading' ? 'Loading…' : 'No curves'}
        </text>
      {/if}
    </svg>
  </div>

  <ul class="legend">
    <li><svg width="28" height="10" aria-hidden="true"><line class="measured" x1="1" x2="27" y1="5" y2="5" /></svg>Measured CoC4</li>
    <li><svg width="28" height="10" aria-hidden="true"><line class="base" x1="1" x2="27" y1="5" y2="5" /></svg>Starting model</li>
    <li class:off={!variantPath}>
      <svg width="28" height="10" aria-hidden="true"><line class="variant" x1="1" x2="27" y1="5" y2="5" /></svg>Changed model
    </li>
  </ul>
</div>

<style>
  .sensitivity-check {
    border: 1px solid var(--line, #e0e0e0);
    border-radius: 6px;
    padding: 1rem;
    margin: 1.5rem 0;
    font-size: 14px;
    color: var(--ink, #222);
    max-width: 100%;
    min-width: 0;
  }
  .hint {
    color: var(--muted, #777);
    margin: 0 0 0.75rem;
  }
  .params {
    border: 1px solid var(--line, #e0e0e0);
    border-radius: 4px;
    margin: 0 0 0.75rem;
    padding: 0.4rem 0.75rem 0.6rem;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 14rem), 1fr));
    gap: 0.2rem 1rem;
    min-width: 0;
  }
  .params legend {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--muted, #777);
    padding: 0 0.3rem;
  }
  .params label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    cursor: pointer;
  }
  .params:disabled label {
    cursor: default;
    opacity: 0.55;
  }
  input[type='radio'] {
    accent-color: var(--accent, #1a5276);
    margin: 0;
  }
  .step {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .step label {
    font-weight: 600;
  }
  input[type='range'] {
    flex: 1;
    min-width: 0;
    max-width: 22rem;
    accent-color: var(--accent, #1a5276);
  }
  input:focus-visible {
    outline: 2px solid var(--accent-2, #2980b9);
    outline-offset: 2px;
  }
  .readout {
    margin: 0.4rem 0 0.6rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    min-height: 1.55em;
  }
  .chart {
    width: 100%;
    min-width: 0;
  }
  .chart svg {
    display: block;
    max-width: 100%;
    height: auto;
    background: var(--fig-bg, #fff);
  }
  .grid {
    stroke: var(--line, #e0e0e0);
    stroke-width: 1;
  }
  .axes {
    fill: none;
    stroke: var(--fig-stroke, #334155);
    stroke-width: 1;
  }
  .tick {
    font-size: 12px;
    fill: var(--ink, #222);
    font-variant-numeric: tabular-nums;
  }
  .title {
    font-size: 13px;
    fill: var(--ink, #222);
  }
  .status {
    font-size: 13px;
    fill: var(--muted, #777);
  }
  .measured {
    fill: none;
    stroke: #b9c0c9;
    stroke-width: 1;
  }
  .base {
    fill: none;
    stroke: var(--c-deeper, #52606d);
    stroke-width: 1.3;
    stroke-dasharray: 5 3;
  }
  .variant {
    fill: none;
    stroke: var(--accent, #1a5276);
    stroke-width: 1.7;
  }
  path {
    stroke-linejoin: round;
  }
  .legend {
    list-style: none;
    margin: 0.5rem 0 0;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem 1.2rem;
    font-size: 13px;
  }
  .legend li {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  .legend li.off {
    opacity: 0.4;
  }
</style>
