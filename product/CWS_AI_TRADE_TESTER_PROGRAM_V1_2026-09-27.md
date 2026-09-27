# CWS AI Trade — Tester Program V1

## Goal

Allow trusted friends/research testers to use CWS AI Trade deeply without granting permanent free access.

## Account model

A tester is still a normal customer identity.

Temporary entitlement:
- role: TESTER
- trial access: full paper + DEMO feature set
- default duration: 30 days
- live/funded execution remains subject to separate hard gates
- no permanent free entitlement

At expiry:
- tester role ends automatically
- account falls back to the normal customer plan
- normal free quota / billing rules apply

Founder has supreme entitlement control at any time, independent of expiry.

Founder may immediately:
- revoke Tester privileges;
- convert the account to CUSTOMER_FREE;
- convert the account to CUSTOMER_PAID;
- suspend access;
- extend Tester access by a fixed duration.

These actions take effect immediately from server-side entitlement state and do not wait for the tester expiry date.

## Why time-based instead of trade-count-only

Tester goal is product validation, not consumption accounting.

A fixed trade quota can be distorted by market regime:
- quiet market -> tester cannot meaningfully exercise the product
- active market -> quota disappears too quickly

Therefore:
- trusted tester access should be time-limited
- customer free tier may still use a trade quota

## Recommended default

- TESTER_FULL
- 30 days
- paper: unlimited within reasonable system limits
- DEMO: enabled
- live money: disabled unless separately approved
- brokerOrders: false unless the normal execution gate permits it
- auto-renew: false

## State machine

Automatic path:
INVITED
-> ACTIVE_TESTER
-> EXPIRED
-> CUSTOMER_FREE

Founder override path, available at any moment:
ACTIVE_TESTER -> CUSTOMER_FREE
ACTIVE_TESTER -> CUSTOMER_PAID
ACTIVE_TESTER -> REVOKED
ACTIVE_TESTER -> SUSPENDED
ACTIVE_TESTER -> EXTENDED

Founder override has precedence over remaining tester time.

Example:
- tester has 27 days remaining;
- Founder changes entitlement to CUSTOMER_FREE;
- Tester privileges stop immediately;
- the previous tester expiry timestamp no longer grants access.

Expiry is a safety backstop, not the source of Founder authority.

## Security

Tester identity must be unique and revocable.
Prefer Google-authenticated user identity once Google Login is implemented.

Never grant:
- GitHub Core access
- research vault access
- production secrets
- customer data from other users
- permanent founder/admin capability

## Audit

Record:
- who granted access
- granted_at
- expires_at
- revoked_at
- reason
- previous/new entitlement state

The entitlement decision must come from server-side state, never only from frontend flags.


## Founder precedence rule

Effective entitlement is evaluated server-side in this order:

1. explicit Founder override
2. suspension/revocation state
3. active Tester entitlement with valid expiry
4. normal customer plan

A valid future tester expiry must never override a newer Founder downgrade.

All Founder entitlement changes must be auditable with:
- actor
- timestamp
- old state
- new state
- optional reason
