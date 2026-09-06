# DNL Backend — Build Plan (Missing Pieces)

Derived from `dnl_website_scope.md` vs. current backend. Ordered by dependency and
business priority. Every phase follows the house conventions in `CLAUDE.md`:
strict serializer validation, fat services / thin views, explicit fields,
`select_related`/`prefetch_related`, TDD with `pytest-django` + `factory_boy`,
`IsAdminUser` for dashboard / throttled `AllowAny` for public.

Legend: 🟥 not started · 🟨 partial · ⬜ infra · ✅ done

> **Progress:** Phases 0–6 are **implemented and tested** — full suite
> 159 passing, 97% coverage. **All scoped backend work in this plan is complete.**
> - Phase 0: email/notifications infra + JWT auth.
> - Phase 1: customers app + orders complete (customer capture, guest matching,
>   admin notes, order-email notification).
> - Phase 2: testimonials (public pending submit + email, admin moderation/reorder,
>   approved-only public reads).
> - Phase 3: careers (admin Job CRUD, auto-slug, published-only public reads;
>   apply stays mailto/off-platform).
> - Phase 4: price list (admin PDF upload via core.storage/R2, public no-login
>   current-metadata + download-redirect, history preserved).
> - Phase 5: enquiries (public contact-form create → logged + emailed to
>   DNL_GENERAL_INBOX, admin log with handled toggle).
> - Phase 6: consolidation — Article cover-image migrated off Django ImageField to
>   an R2 key via core.storage, derived `read_time`, all new models registered in
>   Django admin, notifications matrix audited.
>
> Possible follow-ups (not in original scope gaps): blog article `category` field
> (frontend shows blog categories; Article has none yet); structured price-list
> auto-generation (2.1 open question); loyalty rewards engine (explicitly deferred).

---

## Phase 0 — Foundations (unblocks everything else) ✅

Nothing in the scope's notification layer can ship without these. Do first.

### 0.1 Email / notifications infrastructure ✅
Built: `core/notifications/` (`send_email` service + idempotent `send_email_task`
with capped backoff + `enqueue_email` on-commit helper); EMAIL_* settings + inbox
routing (`DNL_*_INBOX`); Celery autodiscovery of `core.notifications`.
- Add `EMAIL_BACKEND` + SMTP settings via `django-environ` (`EMAIL_HOST`,
  `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `EMAIL_PORT`,
  `EMAIL_USE_TLS`). Console backend in dev, SMTP in prod.
- Add inbox routing config: `DNL_ORDER_INBOX`, `DNL_GENERAL_INBOX`,
  `DNL_CAREERS_INBOX`, `DNL_ADMIN_INBOX` (all from `.env`).
- New `core/notifications/` module: a `send_notification(subject, template, context, to)`
  helper wrapping `django.core.mail` + templated HTML/text bodies.
- Make sends **async + idempotent** via a Celery task (`bind=True`, capped
  `self.retry()` with backoff, PKs not instances) — reuses the existing Celery setup.
- Tests: task retry on failure, correct recipient routing, eager-mode send.

### 0.2 Customer auth / accounts scaffolding ✅
Built: SimpleJWT wired into DRF auth classes; `/api/auth/register|login|refresh|me/`.
Admin stays on `IsAdminUser`; customer endpoints on `IsAuthenticated`.
Required by 2.4 and the logged-in path of 2.6.
- Decide auth: **DRF SimpleJWT** for customer accounts (admin keeps session/admin).
  Add `djangorestframework-simplejwt` to `requirements.txt`.
- Endpoints: register, login (token), refresh, `me` (order history).
- Keep admin endpoints on `IsAdminUser`; customer endpoints on `IsAuthenticated`.

---

## Phase 1 — Orders complete + Customers (highest business value) ✅

Scope 2.6 + 2.4. The booking core exists but can't record *who* ordered or notify.

### 1.1 New `customers` app ✅
- `Customer` model: `name`, `email` (indexed), `phone` (indexed), optional linked
  `User` (nullable OneToOne — guests have none), `created_at`.
- `UniqueConstraint` / lookup strategy: match guest orders to an existing customer
  when **email or phone** matches (service: `match_or_create_customer(...)`).
- Derived-on-read `is_returning` (has >1 order) — never stored.
- Admin list endpoint: total orders, first order date, last order date, new/returning tag.
- Loyalty = **visibility only** for now (scope defers the rewards engine).

### 1.2 Extend `bookings` for real orders ✅
Built: `Booking` now has `customer` (PROTECT), `delivery_location`, `notes`;
guest create-path captures name+email/phone and matches/creates a customer, or
attaches the logged-in customer; order email fires to `DNL_ORDER_INBOX` on commit;
admin PATCH updates status (state machine) and notes; read serializer nests the
customer with the derived `is_returning` tag. Kept `product` required — general
(product-less) enquiries belong to Phase 5. No-oversell row lock intact.
- Add to `Booking`: FK to `Customer` (PROTECT), `delivery_location`,
  `notes` (admin internal), and a nullable `product` to support **general enquiries**
  (product optional) — or a separate `is_enquiry` flag. Decide in review.
- `BookingCreateSerializer`: capture customer contact (name, phone/email, delivery
  location) as guest **or** attach `request.user`'s customer if logged in.
  Call `match_or_create_customer` in the service inside the existing
  `transaction.atomic()` + `select_for_update()` block.
- On successful create → fire order-notification Celery task to `DNL_ORDER_INBOX`
  (Phase 0.1) + on-screen confirmation payload.1
- Admin: status transitions already exist ✅ — add `notes` update + `is_returning`
  flag surfaced in read serializer.
- Tests: guest order, returning-guest match, logged-in order, notification fired,
  no-oversell still holds with the new fields.

---

## Phase 2 — Testimonials (public submit + moderation) ✅

Scope 2.2. Net-new `testimonials` app.

### 2.1 `Testimonial` model ✅
Built with a `CheckConstraint` requiring name-or-company attribution, `rating`
1–5 validated in serializers, `status` (pending/approved/rejected), and
`display_order`. Public reads = approved only, ordered by `display_order`.
- Fields: `reviewer_name`, `company_name` (one of the two required — validate in
  serializer), `body`, optional `role`, `location`, `rating` (1–5),
  `status` (`pending`/`approved`/`rejected`), `display_order` (for reorder),
  `created_at`.
- Public read = approved only, ordered by `display_order` then `-created_at`.

### 2.2 Endpoints ✅
Built: `TestimonialViewSet` — public throttled create (forces pending, returns a
"submitted for review" confirmation) and approved-only reads; admin gets full
list (status filter), approve/edit/reject/delete, reorder (`display_order`), and
unpublish (status→pending). Submit emails `DNL_ADMIN_INBOX` on commit. Public read
serializer omits moderation fields; pending rows 404 for the public. Covered by 14
tests (attribution rule, rating range, pending-not-public, approve→public, reorder,
permission boundaries, notification fired).

---

## Phase 3 — Careers / Job Postings (admin-managed) ✅

Scope 2.3. Net-new `careers` app. Apply stays mailto (out of scope, frontend).

### 3.1 `Job` model ✅
Built: `Job` (title, auto-derived unique `slug`, department, `employment_type`
choices, location, description, requirements, `status` published/unpublished).
`JobViewSet` (`IsAdminOrReadOnly`, slug lookup) — public list/detail = published
only (unpublished 404s), admin full CRUD + publish/unpublish/delete. No public
write path; applications remain off-platform via the applicant's email app.
Covered by 11 tests (slug derivation/uniqueness, visibility, admin CRUD,
permission boundaries).

---

## Phase 4 — Price List (admin-updatable download)

Scope 2.1. Recommend the **file-upload** approach first (simpler, matches "DNL
supplies a PDF"); flag the structured-data auto-gen option as a later discussion.

### 4.1 `PriceList` model ✅
Built: `PriceList` stores the PDF via the **`core.storage` manager** (R2), not a
Django `FileField` — fields `file_key`, `filename`, `content_type`, `uploaded_by`,
`uploaded_at`. History preserved; `PriceList.current()` = latest. `PriceListViewSet`:
admin upload (PDF-validated) + list history; public no-login `current/` (metadata
incl. url + uploaded_at) and `download/` (302 redirect to the storage URL, so the
CDN serves the file). Covered by 9 tests (upload, non-PDF rejection, latest-becomes-
current, public metadata/download, 404-when-none, permission boundaries).
Note: `core.storage.FakeStorage` default base URL changed to an https-style CDN URL
so test redirects pass scheme checks (only substring URL assertions existed).

---

## Phase 5 — Contact / Enquiries

Scope 2.7. Net-new `enquiries` app (backend for the existing contact form).

### 5.1 `Enquiry` model ✅
Built: `Enquiry` (name, email, phone, message, `handled`, created_at) with a
`CheckConstraint` requiring a reply channel (email or phone). `EnquiryViewSet`:
public throttled create → logs the row + emails `DNL_GENERAL_INBOX` on commit,
returns a confirmation; admin list (filter by `handled`), retrieve, mark-handled
(only `handled` writable — the logged message is read-only), delete. No public read
path. Floating WhatsApp/email icons remain frontend-only. Covered by 10 tests
(reply-channel rule, phone-only, log+notify, handled filter/toggle, read-only
message, permission boundaries).

---

## Phase 6 — Admin dashboard consolidation & polish ✅

Scope Section 3. Backend already exposes per-module APIs; this ties them together.
- All modules have admin endpoints: Products ✅, Blog ✅, Orders ✅, Customers ✅,
  Testimonials ✅, Careers ✅, Price List ✅, Enquiries ✅.
- ✅ All new models registered in Django admin for the single-admin account.
- ✅ `read_time` added to `Article` as a **derived** property (words ÷ 200 wpm,
  min 1), exposed read-only in the API and admin.
- ✅ **`Article.cover_image` migrated off Django `ImageField`** → `cover_image_key`
  stored via the `core.storage` manager (R2), consistent with uploads/pricelist.
  Serializer takes an optional multipart `cover_image` on write (Pillow-validated)
  and exposes a derived `cover_image_url` on read. Migration
  `content.0002` removes the old field (no prod data → low risk).
- ✅ Notifications matrix (Section 4) wired: order→`DNL_ORDER_INBOX`,
  testimonial→`DNL_ADMIN_INBOX`, enquiry→`DNL_GENERAL_INBOX`; job apps stay mailto.

---

## Cross-cutting / definition of done
- Migrations kept additive; **no per-category tables** — product custom fields
  (origin, pack sizes, min order qty) live in `attributes` JSONB per the one rule.
- 80%+ coverage per app; unit + integration + permission tests.
- Update `requirements.txt` (SimpleJWT), `.env.example`, and `config/urls.py` includes.
- Security pass: throttling on all public endpoints, no secrets in code,
  input validated in serializers.

## Deployment target: Railway
Affects Phase 0 infra and a few design choices — none block the plan.
- **Redis / Celery:** add a Railway **Redis plugin** and run a **separate worker
  service** (`celery -A config worker`) alongside the web service. Both read the
  same `CELERY_BROKER_URL`/`RESULT_BACKEND` from Railway env. In prod keep
  `CELERY_TASK_ALWAYS_EAGER=False`; the notification + image tasks depend on the
  worker actually running.
- **Postgres:** use the Railway **Postgres plugin**; `django-environ` reads
  `DATABASE_URL`. GinIndex/JSONB all supported.
- **File storage (all media):** Railway containers have an **ephemeral
  filesystem** — uploads must go to external object storage. **Decision:** route
  *all* media through the existing `core.storage` manager (R2) — the "external
  manager" — rather than overriding Django's `STORAGES["default"]`.
  `STORAGES["default"]` stays `FileSystemStorage` and is simply not used for media.
  This means `content.Article.cover_image` must move off Django's `ImageField`
  (see Phase 6) and the Price List (Phase 4) stores an R2 key, matching
  `uploads.Image`. No `django-storages` dependency needed.
- **Email:** SMTP creds as Railway env vars (Phase 0.1). No platform-specific work.
- **Static files:** WhiteNoise is already in `MIDDLEWARE` ✅ — confirm
  `collectstatic` runs in the build/release step.
- **Config:** all secrets via Railway variables → `django-environ`. Keep an
  up-to-date `.env.example`. Set `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` to the
  Railway domain (+ custom domain). Bind web to `$PORT`
  (`gunicorn config.wsgi --bind 0.0.0.0:$PORT`).
- **Release step:** run migrations on deploy via a Railway release/pre-deploy
  command (`python manage.py migrate`) so additive migrations apply automatically.

## Suggested sequencing
`Phase 0` → `Phase 1` (orders+customers, top value) → `Phase 2` (testimonials)
→ `Phase 3` (careers) → `Phase 4` (price list) → `Phase 5` (enquiries)
→ `Phase 6` (consolidation). Phases 2–5 are independent and can be parallelized
once Phase 0 lands.
