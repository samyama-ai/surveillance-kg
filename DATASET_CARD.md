---
license: other
pretty_name: surveillance-kg
tags:
  - knowledge-graph
  - samyama
  - property-graph
  - public-health
language:
  - en
---

# Dataset Card for `surveillance-kg`

**Disease Surveillance Knowledge Graph built from the WHO Global Health Observatory**

> Part of the **Samyama** ecosystem. This card describes the dataset; the repository
> holds the loader and source-data specifics.

## Structure

_Not recorded in this repository's README._ Node labels, edge types and per-label
counts should be added here — a dataset card without them cannot be used to decide
whether the data fits a question.

## Provenance and licence

Apache 2.0 covers the loader. Every node comes from the **WHO Global Health Observatory**,
which is **CC BY-NC-SA 3.0 IGO**: non-commercial, share-alike, crediting WHO. The derived
graph inherits that whole. See [`DATA-LICENSES.md`](DATA-LICENSES.md).


## Freshness

**Refresh cadence:** WHO Global Health Observatory indicators are updated per-indicator,
not on one global calendar — most disease-surveillance and vaccine-coverage indicators
(the ones this repo loads) are revised annually as countries report new figures, with
some indicators revised less often. This repo has no scheduled refresh job; re-running
`etl.download_who` against `https://ghoapi.azureedge.net/api` picks up whatever WHO has
published as of that run.

**Data as of:** This repository ships the loader, not a committed graph — `data/` is
gitignored, so no WHO GHO snapshot is tracked in git history. The best available
evidence is this working copy's local (uncommitted) pull: `data/disease_data.json`'s
own WHO-supplied `Date` field (WHO's last-modified timestamp per record) has a maximum
of **2026-07-14**, and the file's local mtime is 2026-07-25, i.e. WHO's most recent
disease-report update captured by that pull was about 11 days old at fetch time. The
loader code itself was last changed 2026-07-31 (`git log -- etl/`). Because this local
pull isn't part of the repo's git history, a fresh checkout has no data until the
loader is run again — treat 2026-07-14/2026-07-25 as "last known good," not a
guarantee of this moment's freshness.

## Reproducing

The loader in this repository rebuilds the graph from the upstream source. See the
README's Quick Start for the snapshot download and the from-source build.

## Citation

Please cite this repository if you use it. See [`CITATION.cff`](CITATION.cff) for
machine-readable metadata (CFF 1.2.0).

```bibtex
@misc{surveillance_kg_2026,
  title        = {surveillance-kg: Disease Surveillance Knowledge Graph built from the WHO Global Health Observatory},
  author       = {Samyama},
  year         = {2026},
  howpublished = {\url{https://git.samyama.ai/Samyama.ai/surveillance-kg}}
}
```

**No DOI.** This release has not been deposited to Zenodo, so there is no DOI to
cite. Getting one is open work — it requires a human to make the Zenodo deposit
(KG-06).

## Known limitations

- Counts here are those stated by the repository README at the time this card was
  written; they are not re-measured by the card.
- Where a field above says *not recorded*, that is a gap in this repository rather
  than a property of the data.
