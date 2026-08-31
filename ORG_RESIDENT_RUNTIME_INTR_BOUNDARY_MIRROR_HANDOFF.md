# Organization Resident Runtime + Interlock/InTr Boundary Mirror Handoff

Status: ACTIVE
Updated: 2026-08-31
Organization: `Data-Continuation`
Repository: `Data-Continuation/.github`

## Canonical ownership

This `.github` repository owns the organization-level resident-runtime activation source and the mechanism that generates organization ingress and egress communication.

```text
organization resident activation source -> Data-Continuation/.github/org-runtime/
organization ingress generator         -> Data-Continuation/.github/org-runtime/runtime_boundary.py
organization egress generator          -> Data-Continuation/.github/org-runtime/runtime_boundary.py
application repositories               -> endpoint/runtime profiles only
```

All cross-organization communication must cross this boundary as an Interlock/InTr envelope. Application repositories may expose endpoints and capabilities but may not create a second organization ingress/egress authority.

## Runtime boundary

Activation source is kept inside this organization `.github`. Authentic execution remains a sovereign resident process; GitHub and GitHub Actions are source/evidence/validation surfaces only.

```text
source/merge/CI != resident activation
activation request != request consumption
HB presence != execution authority
GitHub token runtime authority = NONE
credential authority = TV/TVC
```

## Communication boundary

Ingress and egress are generated through the same organization-owned mechanism.

```text
peer -> HB/HB-derived carrier -> Interlock -> InTr ingress -> organization resident/runtime profile
organization result -> Transition Element evaluation -> Interlock -> InTr egress -> HB/HB-derived carrier -> peer
```

HB and HB-derived carriers may synchronize and carry packets but grant no admission, execution, credential, routing, transition, receiving, publication, or release authority.

Action admission, authority transfer, capability realization, and authority effect remain distinct. Authority/standing effects are `DERIVED_FROM_APPLICABLE_TRANSITION_ELEMENTS`.

## Machine surfaces

- `org-runtime/activation.json`
- `org-runtime/interlock-intr.json`
- `org-runtime/runtime_boundary.py`

The Python tool is standard-library-only and can:
- validate the boundary contract;
- emit a resident activation request;
- emit ingress envelopes;
- emit egress envelopes.

It does not activate GitHub as runtime and cannot self-grant authority.
