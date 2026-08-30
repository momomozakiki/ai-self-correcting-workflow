# Security — golden rules (code review)

Status: drafted by orchestrator 2026-08-30, unreviewed
Applies when the code handles credentials, untrusted input, authentication, authorization, or
data leaving the process. Ported from `.ai/05-domains/rule-security-review.json` (items resolved
2026-08-05, re-read at port on 2026-08-30).

**How to work these.** They are questions, not prescriptions — do not convert them. A question
makes you look at the code and survives a codebase it was not written for; a prescription tells
you what to type and stops being right the moment the context differs. Report every answer,
including the ones that pass — a checklist that only ever surfaces problems reads as noise.
Where the answer is **"I cannot tell from here"**, say that rather than assuming the safe one.

**What no tool here catches.** This repository's `PreToolUse` guard inspects *commands*, not
file contents, so it cannot see a secret being committed — which is why
`prohibition-commit-secrets` is convention rather than enforced. Scanners catch known shapes;
none of them catches a missing authorization check. These questions are the mechanism.

## When any credential, key or token is involved

- [ ] Is any credential, key or token **literal in source, tests, or an example file**? — move
      it to the environment or a secret store, and **rotate the exposed value**; deleting the
      line does not un-expose it.
- [ ] Does access to each secret follow **least privilege**, or does one credential open
      everything? Issue per-service credentials scoped to what that service reads.
- [ ] Could a secret reach a **log line, an error message, or a stack trace**? — redact at the
      logging boundary, not at each call site, or the next call site will forget.

Sources: OWASP Application Security Verification Standard 5.0.0 — version resolved 2026-08-05,
carried forward unchanged at port on 2026-08-30 and **not independently re-read**. No chapter or
requirement number is given because none was recorded at the original resolution, and inventing
one would look more precise than the citation actually is.

## When ANY untrusted input is received

- [ ] Is validation **enforced on the server**, with client-side checks treated only as
      usability? Re-validate at the trusted service layer.
- [ ] Do database queries use **parameterization, an ORM, or an equivalent protection**? —
      replace concatenation with bound parameters.
- [ ] Is output **encoded for the context it lands in** — HTML body, attribute, CSS, header?
      Use the framework's context-aware encoder rather than one escape function everywhere.
- [ ] Have you **named what is attacker-controlled** here, including data read back from
      storage? List the untrusted inputs before deciding what to validate; data that was
      trusted on the way in is not trusted on the way out.

Sources: OWASP ASVS 5.0.0; OWASP Top 10:2021. Both versions resolved 2026-08-05 and carried
forward unchanged. **Revalidation due:** OWASP Top 10:2025 was in release candidate when these
items were resolved on 2026-08-05 and has not been re-checked here — a release candidate is not
citable as authoritative, and the 2021 edition remains the pinned one until it is.

## When any request acts on data or a privileged function

- [ ] Is **function-level access restricted** to consumers with explicit permission? — check the
      permission in the handler, not only in the route table.
- [ ] Is access checked against **the specific object**, not just the endpoint? Verify the
      caller owns the identifier before acting on it.
- [ ] Does an authorization failure **deny**, or can an error path fall through to allow? —
      default to deny and make the allow explicit.

Sources: OWASP ASVS 5.0.0; OWASP Top 10:2021. Both versions resolved 2026-08-05 and carried
forward unchanged. **Revalidation due:** same OWASP Top 10:2025 release-candidate caveat as
above.

## When adding or updating a dependency

- [ ] Is there an **inventory of third-party libraries** in use? — generate an SBOM in the
      build, so the question "are we affected" has an answer before it is urgent.
- [ ] Are components **within your documented update and remediation window**? Patch, or record
      an accepted exception with a date on it.

Sources: OWASP ASVS 5.0.0 — version resolved 2026-08-05, not independently re-verified at port
on 2026-08-30.
