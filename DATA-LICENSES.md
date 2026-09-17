# Data licences

`LICENSE` in this repository covers the **loader code**. It says nothing about the
upstream data this repository reads and, where a snapshot is published, redistributes.
That gap is what this file closes (samyama-cloud#97).

Each row records what the source's **own terms page** says, with the URL and the date it
was read. Where a source could not be re-verified it says so rather than guessing: an
unverified licence written down as fact is worse than the silence it replaces.

| Source | What we load | What its terms page says | Checked |
|---|---|---|---|
| [WHO Global Health Observatory (OData API)](https://www.who.int/about/policies/publishing/copyright) | Disease surveillance indicators | **CC BY-NC-SA 3.0 IGO.** Copy, adapt and redistribute for **non-commercial** purposes, crediting WHO, with adaptations under the same terms. WHO's logo needs written permission and the data may not be used to promote a product or organisation. | 2026-09-18 |

**Non-commercial and share-alike.** Everything in this graph comes from WHO, so the graph
inherits CC BY-NC-SA 3.0 IGO whole: a published snapshot may be redistributed for
non-commercial use, crediting WHO, under the same licence.

This is why `health-determinants-kg` could not be published to HuggingFace under a
permissive licence (samyama-cloud#122) — the constraint is the same one.

## How to read the "derived graph" line

A graph built from several sources carries **all** of their terms at once. The
restrictive ones win: one non-commercial source makes the join non-commercial, one
share-alike source makes the join share-alike. That is why the derived licence below is
not simply the most permissive source in the table.

## If you redistribute

- Keep the attributions named above with the data.
- State which snapshot version you took, so a reader can check it against the source.
- Re-read the terms pages: licences change, and the dates in this table are when we last
  looked.
