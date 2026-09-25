<script lang="ts">
  import { PARTS, partNavLabel } from '../../lib/parts';
  let { items = [], current = '' }:
    { items?: { slug: string; title: string; part: string; number: string }[]; current?: string } = $props();
</script>
<nav class="chapter-nav">
  {#each PARTS.filter((p) => items.some((i) => i.part === p.key)) as part}
    <p class="part">{partNavLabel(part.key)}</p>
    <ul>
      {#each items.filter((i) => i.part === part.key) as it}
        <li class:active={it.slug === current}>
          <a href={`${import.meta.env.BASE_URL}/${it.slug}`}>{#if it.number !== ''}<span class="ch-num">{it.number}.</span>{' '}{/if}{it.title}</a>
        </li>
      {/each}
    </ul>
  {/each}
</nav>
<style>
  .chapter-nav { font-size: .88rem; }
  .part {
    font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
    font-size: .7rem; color: var(--accent); margin: 1rem 0 .35rem;
  }
  .chapter-nav ul { list-style: none; padding: 0; margin: 0 0 .5rem; }
  .chapter-nav li { margin: .12rem 0; }
  .chapter-nav a { display: block; padding: .12rem 0; text-decoration: none; color: #333; }
  .chapter-nav a:hover { color: var(--accent); }
  .chapter-nav li.active > a { font-weight: 700; color: var(--accent); }
  .chapter-nav .ch-num { color: var(--accent); font-weight: 600; }
</style>
