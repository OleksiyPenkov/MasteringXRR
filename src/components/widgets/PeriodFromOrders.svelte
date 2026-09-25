<script lang="ts">
  import {
    COC4_LAMBDA_A,
    COC4_ORDERS,
    evenTwoTheta,
    fitOrders,
    formatScaled,
    predictTwoTheta,
    withMinus,
    type MeasuredOrder,
  } from '../../lib/period-from-orders';

  // The period and 2δ̄ from the measured Bragg orders: a straight line of
  // sin²θ against m². All the maths is in src/lib/period-from-orders.ts;
  // this component only reads the inputs and displays the result.

  type Row = { id: number; m: string; tt: string };

  let nextId = 0;
  const exampleRows = (): Row[] =>
    COC4_ORDERS.map((o) => ({ id: nextId++, m: String(o.m), tt: String(o.twoThetaDeg) }));

  let lambdaText = $state(String(COC4_LAMBDA_A));
  let rows = $state<Row[]>(exampleRows());

  /** A typed number, with a decimal comma accepted. Blank or junk gives NaN. */
  function parse(s: string): number {
    const t = s.trim().replace(',', '.');
    return t === '' ? Number.NaN : Number(t);
  }

  // A row whose 2θ is still blank is left out, so "Add an order" does not
  // break the result before the reader has typed the angle.
  let orders = $derived<MeasuredOrder[]>(
    rows.filter((r) => r.tt.trim() !== '').map((r) => ({ m: parse(r.m), twoThetaDeg: parse(r.tt) })),
  );
  let lambda = $derived(parse(lambdaText));
  let result = $derived(fitOrders(lambda, orders));

  // The entered orders with their predictions, sorted by m for the table.
  let sorted = $derived.by(() => {
    const r = result;
    if (!r.ok) return [];
    return orders
      .map((o, i) => ({ ...o, pred: r.predicted[i], diff: r.residuals[i] }))
      .sort((x, y) => x.m - y.m);
  });
  // 2θ₁ for the evenly spaced guess: order 1 if entered, else the lowest order scaled down.
  let twoTheta1 = $derived(sorted.length ? sorted[0].twoThetaDeg / sorted[0].m : Number.NaN);
  let lowest2T = $derived(sorted.length ? Math.min(...sorted.map((o) => o.twoThetaDeg)) : Number.NaN);
  // The next two orders beyond the highest entered: where to look for a weak one.
  let nextOrders = $derived.by(() => {
    const r = result;
    if (!r.ok || !sorted.length) return [];
    const mMax = sorted[sorted.length - 1].m;
    return [mMax + 1, mMax + 2].map((m) => ({
      m,
      pred: predictTwoTheta(m, r.D, r.twoDelta, lambda),
      even: evenTwoTheta(m, twoTheta1),
    }));
  });

  // The scan step is 0.003° in 2θ, so a measured position needs four decimals (1.6975°).
  const deg3 = (v: number) => withMinus(v.toFixed(3));
  const deg4 = (v: number) => withMinus(v.toFixed(4));
  function signed4(v: number): string {
    const r = Number(v.toFixed(4));
    if (r === 0) return '0.0000';
    return (r > 0 ? '+' : '−') + Math.abs(r).toFixed(4);
  }

  function addRow() {
    const ms = rows.map((r) => parse(r.m)).filter((m) => Number.isInteger(m));
    const m = ms.length ? Math.max(...ms) + 1 : 1;
    rows.push({ id: nextId++, m: String(m), tt: '' });
  }
  function removeRow(id: number) {
    rows = rows.filter((r) => r.id !== id);
  }
  function reset() {
    lambdaText = String(COC4_LAMBDA_A);
    rows = exampleRows();
  }
</script>

<div class="widget period-from-orders">
  <p class="hint">
    Type the order number m and the measured 2θ of each Bragg order. The results update as you
    type. The example is the Co/C multilayer CoC4, its six clear orders.
  </p>

  <label class="lambda">
    <span>Wavelength λ (Å)</span>
    <input type="text" inputmode="decimal" autocomplete="off" spellcheck="false" bind:value={lambdaText} />
  </label>

  <div class="rows" role="group" aria-label="Measured Bragg orders">
    <span class="col-head" aria-hidden="true">Order m</span>
    <span class="col-head" aria-hidden="true">Measured 2θ (°)</span>
    <span></span>
    {#each rows as row, i (row.id)}
      <input
        type="text"
        inputmode="numeric"
        autocomplete="off"
        spellcheck="false"
        aria-label={`Order number m, row ${i + 1}`}
        bind:value={row.m}
      />
      <input
        type="text"
        inputmode="decimal"
        autocomplete="off"
        spellcheck="false"
        aria-label={`Measured 2θ in degrees, row ${i + 1}`}
        bind:value={row.tt}
      />
      <button
        type="button"
        class="secondary"
        aria-label={`Remove row ${i + 1}`}
        disabled={rows.length <= 1}
        onclick={() => removeRow(row.id)}>Remove</button
      >
    {/each}
  </div>

  <div class="buttons">
    <button type="button" onclick={addRow}>Add an order</button>
    <button type="button" class="secondary" onclick={reset}>Reset to the CoC4 example</button>
  </div>

  <div class="results" aria-live="polite">
    {#if !result.ok}
      <p class="message">{result.message}</p>
    {:else}
      <dl class="readouts">
        <div>
          <dt>Period D</dt>
          <dd>
            {result.D.toFixed(2)}{#if result.sigmaD !== null}&nbsp;± {result.sigmaD.toFixed(2)}{/if}&nbsp;Å
          </dd>
        </div>
        <div>
          <dt>Refraction term 2δ̄</dt>
          <dd>{formatScaled(result.twoDelta, result.sigmaTwoDelta, 2)}</dd>
        </div>
        <div>
          <dt>Critical angle 2θ<sub>c</sub></dt>
          <dd>
            {#if result.twoThetaC !== null}
              {result.twoThetaC.toFixed(3)}{#if result.sigmaTwoThetaC !== null}&nbsp;± {result.sigmaTwoThetaC.toFixed(3)}{/if}°
            {:else}
              none (2δ̄ is not positive)
            {/if}
          </dd>
        </div>
        <div>
          <dt>Rms residual of the line, in sin²θ</dt>
          <dd>{formatScaled(result.rmsSin2, null, 1)}</dd>
        </div>
      </dl>

      {#if result.twoDelta <= 0}
        <p class="message">
          2δ̄ is negative: the orders are probably numbered wrong. Check that the first peak is order 1
          and that no weak order was skipped.
        </p>
      {:else if result.twoThetaC !== null && result.twoThetaC >= lowest2T}
        <p class="message">
          2θ<sub>c</sub> comes out above the lowest order you entered. The critical edge must lie below
          the first order, so the orders are probably numbered wrong. Check that no weak order was
          skipped.
        </p>
      {/if}
      {#if result.n === 2}
        <p class="note">
          With two orders the line passes exactly through both points, so there are no uncertainties.
          Enter a third order to get them.
        </p>
      {/if}

      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">m</th>
              <th scope="col">Measured 2θ (°)</th>
              <th scope="col">Predicted 2θ, with refraction (°)</th>
              <th scope="col">Difference (°)</th>
              <th scope="col">Evenly spaced, m·2θ<sub>1</sub> (°)</th>
            </tr>
          </thead>
          <tbody>
            {#each sorted as o (o.m)}
              <tr>
                <td>{o.m}</td>
                <td>{deg4(o.twoThetaDeg)}</td>
                <td>{o.pred === null ? 'none' : deg4(o.pred)}</td>
                <td>{o.diff === null ? '' : signed4(o.diff)}</td>
                <td>{deg4(evenTwoTheta(o.m, twoTheta1))}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <p class="next-head">Predicted positions of the next orders (not measured):</p>
      <ul class="next">
        {#each nextOrders as o (o.m)}
          <li>
            Order {o.m}:
            {#if o.pred !== null}
              2θ = {deg3(o.pred)}° with refraction (evenly spaced guess: {deg3(o.even)}°)
            {:else}
              no such order for this period and wavelength
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<style>
  .period-from-orders {
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
  input {
    font: inherit;
    color: inherit;
    background: transparent;
    border: 1px solid var(--line, #e0e0e0);
    border-radius: 4px;
    padding: 0.3rem 0.45rem;
    width: 100%;
    min-width: 0;
    font-variant-numeric: tabular-nums;
  }
  input:focus-visible {
    outline: 2px solid var(--accent-2, #2980b9);
    outline-offset: 1px;
  }
  .lambda {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.75rem;
  }
  .lambda input {
    width: 8rem;
  }
  .rows {
    display: grid;
    grid-template-columns: minmax(0, 5rem) minmax(0, 9rem) max-content;
    justify-content: start;
    gap: 0.35rem 0.5rem;
    align-items: center;
  }
  .col-head {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--muted, #777);
  }
  .buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0.75rem 0 1rem;
  }
  button {
    background: var(--accent, #1a5276);
    color: #fff;
    border: 1px solid var(--accent, #1a5276);
    padding: 0.35rem 0.9rem;
    border-radius: 5px;
    font: inherit;
    font-weight: 600;
    cursor: pointer;
  }
  button:hover {
    background: var(--accent-2, #2980b9);
    border-color: var(--accent-2, #2980b9);
  }
  button.secondary {
    background: transparent;
    color: var(--accent, #1a5276);
  }
  button.secondary:hover {
    background: var(--bg-soft, #f7f9fb);
  }
  button:disabled {
    opacity: 0.45;
    cursor: default;
  }
  .readouts {
    margin: 0 0 0.75rem;
    display: grid;
    gap: 0.2rem;
  }
  .readouts div {
    display: flex;
    flex-wrap: wrap;
    gap: 0 0.6rem;
  }
  .readouts dt {
    color: var(--muted, #777);
    min-width: 13rem;
  }
  .readouts dd {
    margin: 0;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }
  .message {
    border-left: 3px solid var(--c-warning, #c62828);
    background: var(--bg-soft, #f7f9fb);
    padding: 0.5rem 0.75rem;
    margin: 0.5rem 0;
  }
  .note {
    color: var(--muted, #777);
    margin: 0.5rem 0;
  }
  .table-scroll {
    overflow-x: auto;
    max-width: 100%;
  }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.5rem 0;
    font-variant-numeric: tabular-nums;
  }
  /* The chapter's table style uppercases the header; that would turn θ into Θ. */
  th {
    text-transform: none;
    letter-spacing: 0;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--muted, #777);
    text-align: right;
    vertical-align: bottom;
    border-bottom: 2px solid var(--line, #e0e0e0);
    padding: 4px 8px 6px;
  }
  td {
    text-align: right;
    padding: 4px 8px;
    border-bottom: 1px solid var(--line, #e0e0e0);
    white-space: nowrap;
  }
  th:first-child,
  td:first-child {
    text-align: center;
  }
  .next-head {
    margin: 0.75rem 0 0.2rem;
  }
  .next {
    margin: 0;
    padding-left: 1.2rem;
  }
</style>
