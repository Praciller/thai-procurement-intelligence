# Production Home Rendered Zero Data

## Summary

The production home page rendered `0` records and empty top-project sections while API endpoints returned 120 records. Fixed by resolving server-side relative API URLs through the public production alias and setting `NEXT_PUBLIC_SITE_URL` in Vercel.

## Symptom

- Home page showed `Records: 0`, `Total budget: THB 0`, and `No records found`.
- `/backend/api/analytics/overview` returned `total_records: 120`.
- `/backend/api/records?page_size=1` returned `total: 120`.

## Root Cause

Server components called `fetch()` with a relative API base (`/backend/api`). In production, that relative base could resolve through a protected deployment URL rather than the public alias. Vercel returned an authentication page for the protected deployment URL, `safeApiFetch()` swallowed the failed response, and the home page rendered the empty fallback.

## Why It Produced The Symptom

Client-visible API routes worked because browser requests hit the public alias. Server-rendered home data failed because the server-side origin differed. The fallback objects in `apps/web/src/lib/api.ts` made the failure look like valid empty data instead of a hard error.

## Fix

- Added `apps/web/src/lib/api-url.js` to resolve server-side relative API paths against `NEXT_PUBLIC_SITE_URL` before falling back to `VERCEL_URL`.
- Set Vercel Production `NEXT_PUBLIC_SITE_URL=https://thai-procurement-intelligence.vercel.app`.
- Added tests for absolute API URLs, browser-relative URLs, server-side Vercel URLs, and configured site URL precedence.

## Validation

- `npm run web:test`: 7 passed.
- `npm run web:lint`: passed.
- `npm run web:build`: passed.
- Production home HTML contained Thai copy, `120`, and `572,142,000`.
- Production browser QA showed English and Thai home pages with real data and no console errors.
- `/backend/api/health/readiness` returned `record_count: 120`.

## Why It Slipped Through

Local development used either an absolute API URL or a localhost relative route, so the protected deployment URL path was not exercised. CI covered build and unit paths but did not perform production alias smoke checks.

## Follow-Ups

- Production readiness endpoint added.
- Deployment docs now require `NEXT_PUBLIC_SITE_URL` for Vercel Services.
- CI now runs API tests, web unit tests, lint, and production build on every push and pull request.
