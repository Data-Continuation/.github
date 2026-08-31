# Organization Resident Runtime / Interlock-InTr Handoff

Organization: **Data-Continuation**  
Runtime owner: **Data-Continuation/.github**

## Canonical rule

All Data-Continuation resident-runtime activation declarations, runtime activation requests,
and organization-boundary ingress/egress mechanisms are owned by this `.github`
repository.

Sibling repositories may implement application behavior, but they may not become
an independent organization runtime owner or create an alternate cross-boundary
transport authority.

Every cross-boundary communication must pass through:

```text
organization-local .github runtime boundary
  -> Interlock validation/construction
  -> governed InTr packet
  -> HB / deterministic HB-derived carrier where available
  -> receiving Interlock
```

HB and derived carriers grant no admission, execution, credential, routing,
transition, publication, or receiving authority. InTr transport also grants no
execution authority. Credential authority remains TV/TVC.

## Machine surfaces

- `control/organization-runtime.json` — machine-readable ownership/profile.
- `runtime/organization_runtime.py` — local activation + Interlock/InTr
  ingress/egress mechanism.
- `runtime/activations/` — write-once activation requests/receipts.
- `runtime/egress/` — write-once organization egress envelopes.
- `runtime/ingress/` — write-once validated ingress receipts.

GitHub Actions may validate these files but is not the resident runtime.
Source presence does not prove deployment, activation, observation, or completion.
