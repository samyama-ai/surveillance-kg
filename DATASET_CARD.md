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


## Reproducing

The loader in this repository rebuilds the graph from the upstream source. See the
README's Quick Start for the snapshot download and the from-source build.

## Known limitations

- Counts here are those stated by the repository README at the time this card was
  written; they are not re-measured by the card.
- Where a field above says *not recorded*, that is a gap in this repository rather
  than a property of the data.
