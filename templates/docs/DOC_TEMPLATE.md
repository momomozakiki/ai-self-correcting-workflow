---
title: <Title>
version: 1.0
last_validated: YYYY-MM-DD
official: false
source: agent-generated
tags: [<retrieval-tags>]
applies_when: "<one line: when is this doc the right thing to load?>"
estimated_tokens: <int>
---

<!--
  HOW TO USE THIS TEMPLATE (delete this comment before saving)
  - Copy this file into your documentation directory and fill every <placeholder>.
  - Frontmatter fields (see GUIDE.md §6):
      title           Human title, matches the H1 below.
      version         MAJOR.MINOR. Bump MINOR for content, MAJOR for a restructure.
      last_validated  Date you last confirmed the content is correct (YYYY-MM-DD).
      official        true  = reviewed/approved via governance (e.g. GUIDE.md, ADRs)
                      false = draft / agent-generated / notes / checkpoint
                      unknown = origin not yet confirmed
      source          URL | agent-generated | user-provided, origin unknown
      tags            Lowercase retrieval tags used by the Progressive Disclosure script.
      applies_when    When this doc should be pulled into context.
      estimated_tokens  Honest token estimate; feeds retrieval + the token-budget lint.
  - On every non-trivial edit: bump version, refresh last_validated, add a Revision History row.
  - JSON / code files can't hold frontmatter — use a sidecar <file>.prov.md instead (GUIDE.md §6.2).
  - If this doc grows past its layer's token budget or covers more than one question,
    split it per docs/Progressive Disclosure Documentation Guide.md (§2, §5).
-->

# <Title>
**Version 1.0** — *<one-line scope>*

## Revision History
| Version | Date       | Change   |
|---------|------------|----------|
| 1.0     | YYYY-MM-DD | Initial. |

---

<!-- Document body starts here. Keep it answering one clear question. -->
