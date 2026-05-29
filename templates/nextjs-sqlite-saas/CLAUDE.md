# Next.js 15 + SQLite SaaS Project Guide

Use this file as the operating contract for a greenfield SaaS built with Next.js 15 App Router, TypeScript, React Server Components, and SQLite via `better-sqlite3` locally or Turso/libSQL in production.

## Stack And Versions

- Next.js 15 App Router with TypeScript in strict mode.
- React Server Components by default; client components only where browser state, effects, or event handlers are required.
- SQLite as the source of truth. Use `better-sqlite3` for local single-process apps and Turso/libSQL when deployed to serverless or edge-like environments.
- Drizzle ORM is preferred for schema, migrations, and typed queries. Raw SQL is allowed for reporting queries when it is clearer than ORM composition.
- Zod validates all external input before it reaches database code.
- Vitest covers pure business logic and database helpers. Playwright covers critical SaaS flows such as signup, billing-gated access, and settings updates.

## Folder Structure

```text
app/
  (auth)/
  (dashboard)/
  api/
components/
  ui/
  forms/
db/
  client.ts
  schema.ts
  migrations/
features/
  accounts/
  billing/
  projects/
lib/
  auth.ts
  env.ts
  permissions.ts
tests/
```

Keep route files thin. A route should compose data loading, validation, and UI; it should not contain durable business rules. Put product logic in `features/<domain>` so it can be tested without rendering a Next.js route.

## Naming Conventions

- Use `camelCase` for TypeScript variables and functions.
- Use `PascalCase` for React components and exported types.
- Use `snake_case` for SQLite table and column names. SQLite is easier to inspect and migrate when SQL names stay SQL-shaped.
- Name server actions by the event they perform, such as `createProjectAction`, not by implementation details like `insertProject`.
- Name database helpers after the domain behavior, such as `getProjectsForAccount`, not generic names like `queryProjects`.

## Database And Migration Rules

- Every schema change must include a migration in `db/migrations`.
- Migrations are append-only. Never edit a migration that has shipped; create a new migration instead so local, preview, and production databases converge predictably.
- Enable foreign keys on every SQLite connection with `PRAGMA foreign_keys = ON`.
- Store timestamps as ISO-8601 UTC text unless there is a measured reason to use integer epochs. Human-readable timestamps make support and backups easier.
- Prefer explicit indexes for foreign keys and dashboard filters. SQLite will not rescue slow account-scoped queries automatically.
- Do not use destructive migrations such as dropping columns or tables without a copy-and-backfill plan.
- Wrap multi-step writes in transactions. Account creation, subscription changes, and permission updates must either fully commit or fully roll back.

## Data Access Pattern

- UI reads call server-side query functions from `features/<domain>/queries.ts`.
- Mutations go through server actions in `features/<domain>/actions.ts`.
- Database writes validate input with Zod before opening a transaction.
- Never call the database directly from client components.
- Scope every SaaS query by `account_id` or `user_id`. Missing tenant scope is a security bug, not a cleanup task.

## Component Patterns

- Server components fetch data and pass small, serializable props down.
- Client components are reserved for interactivity: menus, form state, optimistic updates, dialogs, and charts that need browser APIs.
- Keep reusable primitives in `components/ui`; keep product-specific UI in `features/<domain>/components`.
- Forms should use a shared pattern: Zod schema, server action, pending state, error summary, and field-level errors.
- Avoid fetching from internal API routes when a server component can call the query function directly. API routes are for external callers, webhooks, and browser-only integrations.

## Authentication And Permissions

- Treat authentication and authorization as separate layers.
- Authentication identifies the user. Authorization checks what that user can do inside the current account.
- Put role and permission checks in `lib/permissions.ts`.
- Never trust account IDs sent from the client without verifying membership on the server.
- Webhook handlers must verify provider signatures before parsing business payloads.

## Environment And Secrets

- Define required environment variables in `lib/env.ts` and validate them at process startup.
- Do not read `process.env` throughout the app. Import typed config from `lib/env.ts`.
- Keep local `.env` values out of commits.
- Separate local SQLite paths from production Turso/libSQL URLs so deployments cannot accidentally write to local files.

## Dev Commands

```bash
npm run dev          # start Next.js locally
npm run db:generate  # generate migrations from schema changes
npm run db:migrate   # apply migrations
npm run test         # run unit tests
npm run test:e2e     # run Playwright flows
npm run lint         # lint and type-check
```

If a command is missing, add it to `package.json` before relying on it in docs or CI.

## Anti-Patterns To Avoid

- Do not put business logic in `app/**/page.tsx`. Pages should orchestrate, not own policy.
- Do not make every component a client component. That gives up App Router's main advantage and increases shipped JavaScript.
- Do not build a generic repository abstraction over SQLite on day one. Start with domain-specific query functions and extract only when repetition is real.
- Do not silently create database columns from optional UI fields. Defaults belong in schema and migrations, not scattered form handlers.
- Do not use broad `SELECT *` in account-scoped screens. Explicit columns make privacy reviews and performance tuning easier.
- Do not catch and swallow database errors. Convert expected constraint failures into user-facing messages; let unexpected failures surface to logging.

## Definition Of Done

- New routes load without client-side waterfalls.
- New mutations validate input, enforce permissions, and run inside transactions when writing multiple records.
- New schema changes include migrations and at least one test or documented manual verification.
- User-facing flows include empty, loading, error, and success states.
- Code is tenant-scoped, typed, and usable by Claude Code without extra project explanation.
