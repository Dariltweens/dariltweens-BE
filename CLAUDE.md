# CLAUDE.md

Guidance for working on this codebase. Read this before writing or reviewing code.

## Project

Backend for a product dashboard. The client currently sells **fish (fresh & frozen)**, but the platform must scale to additional categories (poultry, vegetables, etc.) **without backend restructuring, schema rewrites, or repeated migrations**. Category-specific behavior must never be hardcoded.

## Stack

| Layer | Choice |
|---|---|
| Framework | Django (latest LTS) |
| API | Django REST Framework |
| Database | PostgreSQL |
| Task queue | Celery (Redis broker) — for image optimization, async work |
| Storage | Cloud object storage (e.g. S3) via `django-storages` |
| Settings | `django-environ` + `.env` |
| Packaging | pip + pinned `requirements.txt` (+ `requirements-dev.txt`) |

## The one rule that governs the whole design

**Adding a new category must require zero code changes and zero migrations.** A category defines its own custom fields; products store those fields as data, not columns.

- `Category` holds a **schema definition** (field name, type, required, choices, validation) — stored as JSONB.
- `Product` holds an **`attributes` JSONField** validated at write time against its category's schema in the serializer.
- Never add per-category models, columns, or `if category == "fish"` branches. If you find yourself special-casing a category, stop — it belongs in the category's schema.
- Use `GinIndex` on the `attributes` JSONB field for queryable custom fields.

Example: Fish schema defines `freshness`, `size_range`; Poultry defines `breed`, `weight_range`. Same tables, different schema rows.

## Apps / domain

- **catalog** — `Category` (name, slug, `field_schema` JSONB), `Product` (name, description, price, category FK, `attributes` JSONB, images, stock quantity, low-stock threshold). Stock status (`in_stock` / `low_stock` / `out_of_stock`) is **derived** from quantity + threshold, never stored as a field.
- **content** — `Article` (title, content, cover image, status `draft`/`published`). Public reads see published only.
- **bookings** — `Booking` (product FK, quantity, pickup_date, status `pending`/`confirmed`/`cancelled`/`fulfilled`). Public create; admin manages status.
- **media/uploads** — image upload + async optimization to cloud storage.

## Access control

- Admin dashboard endpoints: `IsAdminUser` (staff/admin only), login-protected.
- Public endpoints (browse products, read published articles, submit bookings): `AllowAny`, but **throttled**.
- Default to locked-down; open up explicitly per endpoint. Never rely on `DEFAULT_PERMISSION_CLASSES` being permissive.

## Conventions (from the django-backend skill — follow these)

1. **Strict serializer validation.** All input validation lives in serializers (`validate_<field>`, `validate()`), never in views. Category attribute validation happens here — validate `attributes` against `category.field_schema`.
2. **Fat models / services, thin views.** Multi-model or side-effecting logic goes in `services.py`. Booking stock checks, category schema validation helpers, etc.
3. **QuerySet hygiene.** Always `select_related`/`prefetch_related` (e.g. `Product` → `category`). No N+1 in `SerializerMethodField`. `db_index=True` on FKs used in filters.
4. **Explicit serializer fields.** List fields explicitly; never `fields = "__all__"`. Mark `id`, `created_at`, derived stock status `read_only`.
5. **Idempotent Celery tasks.** Pass PKs not instances; `bind=True` + capped `self.retry()` with backoff. Image optimization is the main async task.
6. **Data integrity.** Correct `on_delete` (products → category likely `PROTECT`; bookings → product `PROTECT`). Wrap booking creation (stock decrement) in `transaction.atomic()` + `select_for_update()` to avoid overselling. `UniqueConstraint`/`slug` uniqueness on categories.
7. **DRF read/write split.** Nested category on read, `category_id` (`PrimaryKeyRelatedField`, `write_only`) on write.
8. **Filtering** via `django-filter` (products by category, stock status, price).

## Bookings — watch for

- Reserving quantity must not oversell. Lock the product row, re-check available stock inside the transaction, then create the booking.
- Status transitions are admin-only and should be validated (e.g. can't fulfil a cancelled booking).

## Testing

`pytest-django` + `factory_boy`. Cover: category schema validation (valid + invalid attributes), stock-status derivation, booking concurrency/oversell, article draft-vs-published visibility, and permission boundaries (public vs admin).

## When in doubt

Ask: "Does this make it harder to add a category later?" If yes, redesign. Extensibility and avoiding future migrations are the primary success criteria for this build.
