# Contributing to AI-TRADE

AI-TRADE uses least-privilege collaboration.

## Default contributor scope

External collaborators should work only on the minimum surface required for their assigned task.

Typical UI contributor scope:
- `dashboard/`
- sanitized contracts / fixtures
- design assets

Do not request or use:
- broker passwords;
- Supabase service-role secrets;
- Vault contents;
- customer financial-account credentials;
- proprietary private research datasets;
- production deployment credentials.

## Change workflow

1. Work on a feature branch.
2. Keep changes scoped to one feature group.
3. Open a pull request.
4. Sensitive paths require Founder review.
5. No direct production deployment by ordinary contributors.
6. No secrets in commits, issues, screenshots, logs, or PR descriptions.

## Strategy boundary

UI/product work must consume a sanitized API contract.

A collaborator should not need the underlying proprietary strategy implementation just to build:
- login;
- dashboard;
- charts;
- billing;
- account settings;
- notifications.

## Data boundary

Use synthetic/sanitized fixtures for development whenever possible.

Never copy raw customer trading-account data into:
- local fixtures;
- test repos;
- screenshots;
- issue bodies.

## Security incident rule

If a secret is accidentally exposed:
- stop using it;
- revoke/rotate it;
- remove it from current code;
- treat repository history as compromised until remediated.

Git history deletion alone is not a substitute for secret rotation.
