# Core-Lite exact pinned-source rights and contributor audit — 2026-09-25

Existing parent goal: `ECOSYSTEM-OPEN-SOURCE-STRATEGY-001`, COSV `20010010100000`. This is Data-Continuation's source-owned evidence report, not a new goal or license grant.

## Exact SDK dependency
`StegVerse-org/StegVerse-SDK` optional extra `governed-test` declares `stegverse-core-lite @ git+https://github.com/Data-Continuation/core-lite.git@72bdb0f110031ccc2cd98b8ebb7c22b1ab7326f8`. The pinned commit resolves; its GitHub commit records StegVerse as author, dated 2026-08-13T17:49:13Z, with two parents. This confirms the pinned object is reachable, **not** that downstream redistribution is authorized.

The complete recursive pinned tree request returned 335 entries with `truncated=false`. No path matching `LICENSE`, `LICENCE`, `NOTICE`, common vendor/dependency lockfile or git submodule declaration appeared. Exact-commit root directory also has no LICENSE/NOTICE. Pinned `pyproject.toml` blob `3ba3dcc4f89f56613147ceae66bc1cc3695ca729` declares project `stegverse-core-lite`, version 0.9.0, Python >=3.11 and build requirement `setuptools>=68`; it has no `license` field and no declared project runtime dependencies. A missing root license is not a legal conclusion about all files or earlier grants. Current `main` also has no root LICENSE, as observed.

## Reachable commit attribution — bounded GitHub history census

GitHub `/commits?sha=<pinned>&per_page=100&page=N` yielded four pages of 100, 100, 100 and 51, then an empty fifth page. Among the **351 returned commits**, GitHub commit attribution was:
- 336 authored as StegVerse (GitHub noreply identity);
- 14 authored as Data-Continuation Core-Lite Manager (automation role);
- 1 authored as github-actions[bot].

These are **Git commit author strings, not proof of legal authorship**. Commits can include merges, imports and generated content. There was no contributor permission/assignment, employment/contractor rights review, original file-origin reconstruction, coauthor trailer audit or independent provenance attestation. The reachable commit result provides a useful input ledger but not a completed copyright chain.

## Import and third-party source observations

Twenty `core_lite/*.py` package modules from the exact pinned tree were individually inspected for literal top-level `import` and `from` statements. The observed statements reference Python standard library modules or the package's own `core_lite` modules; no third-party top-level imports were observed in the sampled files. One package module contains `try:` imports; this literal-line inspection does **not** exclude delayed imports, imports inside functions, scripts, fixtures, generated code or uninspected modules. The pinned `pyproject.toml` names setuptools as a build dependency. Tree path scanning found no obvious vendored or lockfile paths; exhaustive content/SBOM/license-compatibility and imported-code provenance remain unverified.

## Exact actionable dispositions

1. **SOURCE_LICENSE_SCOPE_UNVERIFIED**: The exact pinned 0.9.0 commit has no root LICENSE and no project license declaration. Obtain source-owner and actual rights-holder-approved exact file/version license map; inspect historical releases and source headers. Do not unilaterally add a license.
2. **CONTRIBUTOR_CHAIN_UNVERIFIED**: Reconstruct and independently attest file origins, bot/manager activity, potential coauthored and imported work, and the actual rights-holder assignments. The commit-count census alone cannot clear rights.
3. **DEPENDENCY_PROVENANCE_PARTIAL**: Generate a pinned-version SBOM including setuptools, optional/lazy dependencies, test/tooling and any third-party source; verify rights, distribution boundaries and build reproducibility with the parent SDK.
4. **OPTIONAL_PYTHON_COMPATIBILITY_REVIEW**: SDK metadata supports Python >=3.9 while exact pinned Core-Lite requires >=3.11. Preserve core SDK compatibility and specify/test optional-extra eligibility without changing existing dependencies as part of this rights inventory.
5. **RELEASE_NOT_AUTHORIZED**: No new license grant, relicensing, new release, installation/runtime result, authenticated InTr admission or Master Records closure was obtained. Source evidence remains nonterminal until authorized owner remediation and applicable governance receipts.

Source owner controls any subsequent Core-Lite source changes. Central owner only aggregates a public-safe count and these source-level disposition classes, not private repository names.

## 2026-09-25 follow-up — owner remediation initiated, not cleared

Source owner [Core-Lite issue #34](https://github.com/Data-Continuation/core-lite/issues/34) now holds the pinned-source remediation predicates. [Core-Lite draft PR #35](https://github.com/Data-Continuation/core-lite/pull/35) adds an exact-scope rights-holder decision form and README / canonical source handoff references. Independently re-read pinned `pyproject.toml` blob `3ba3dcc4f89f56613147ceae66bc1cc3695ca729`: Core-Lite v0.9.0, Python >=3.11, setuptools>=68, license field absent; checked SDK `pyproject.toml` retains Python >=3.9 base and exact optional Core-Lite pin `72bdb0f110031ccc2cd98b8ebb7c22b1ab7326f8`. The original 335 pinned tree paths, 351 reachable commit attribution records and sampled top-level imports remain bounded audit inputs; no new assignment instrument or independent rights-holder approval has been retrieved.

Owner dispositions remain `DENY:SOURCE_LICENSE_SCOPE_UNVERIFIED`, `DENY:CONTRIBUTOR_CHAIN_UNVERIFIED`, `DENY:DEPENDENCY_PROVENANCE_PARTIAL`, `DENY:OPTIONAL_PYTHON_COMPATIBILITY_REVIEW`, and `DENY:RELEASE_NOT_AUTHORIZED`. Do not promote PR #35 as merged or source/legal clearance before approved exact-head review and source readback. On authenticated source-owner evidence, append original file/version grant scope and predecessor-linked proof here; send only aggregate-safe status to [central draft #2750](https://github.com/StegVerse-Labs/.github/pull/2750) under existing goal/COSV. No license mutation, release or runtime claim.
