SCOPE OF WORK
Dariltweens Nigeria Limited — Website Platform Enhancement
Prepared for review and sign-off  |  22 August 2026

This document defines the full functional scope for the DNL website beyond what is already visible on the live frontend build. It is intended to align on exactly what the platform will do — for site visitors, returning customers, and DNL staff/admin — before backend and CMS development begins.

Live frontend reference: https://dariltweens.vercel.app (Home, About, Products, Blog, Careers, Contact)
1. Purpose & Current State

The frontend design and page structure for the DNL website have already been built and are live at the link above. Content currently shown on the site — products, blog articles, job openings, and customer testimonials — is static/placeholder content wired directly into the frontend. This scope defines the backend, admin dashboard, and dynamic functionality required to turn this into a fully self-manageable, world-class business platform.

Already implemented on the frontend (static/placeholder)
• Homepage, About, Products, Blog, Careers, and Contact pages, fully designed and responsive.
• Product listing and detail pages (currently 4 fixed seafood products with fixed specs).
• Blog listing and article pages (currently 6 fixed articles with categories).
• Careers page listing 5 fixed job openings, each with a detail page and a working “mailto” apply link that opens the applicant's email app with a pre-filled application template.
• Testimonials carousel on the homepage (currently fixed/hardcoded reviews, not user-submitted).
• Contact page with a general enquiry form, phone, email, address/map link, and an “Open Order Form” call-to-action.
• A WhatsApp link in the footer and a dedicated “WhatsApp Us” button with a pre-filled message.
• “Download Price List” and “Place an Order” entry points already placed in the header and footer, not yet wired to a backend.
Everything above proves out the design and UX. What's scoped below is the functional layer — the CMS, admin dashboard, database, and notification logic — that DNL needs to run the site as a real business tool without depending on a developer for day-to-day updates.


2. Detailed Feature Scope

2.1 Downloadable, Admin-Updatable Price List

Current build status: Static “Price List” / “Download Price List” links exist in the header and footer but are not yet connected to a real file or backend.

Objective: Let visitors download the current, always-up-to-date DNL price list without DNL needing a developer to change it.
User-facing functionality
• “Download Price List” button (header, footer, and product pages) downloads the current file as a PDF.
• Download does not require login or account creation.
Admin-facing functionality
• Admin can upload a new price list file (PDF) from the dashboard at any time; the live download link updates instantly.
• Admin can see the date the current price list was last updated.
• (Optional, for discussion) Admin can instead maintain prices as structured data per product, with a PDF auto-generated — more work, but keeps prices consistent with the product pages.
Notes
• Recommend confirming with DNL whether they'll always supply a ready-made PDF, or want prices generated from product data directly — this changes the build approach.
2.2 Customer Testimonials (Public Submission + Admin Moderation)

Current build status: Testimonials are currently hardcoded on the homepage — not submitted by real users, and no submission form exists yet.

Objective: Let real customers submit reviews, while DNL controls exactly what appears publicly.
User-facing functionality
• Any visitor can submit a testimonial — no account or login required.
• Required fields: reviewer name and/or company name, plus the testimonial text.
• Optional fields: role/title, location, star rating.
• Submitted testimonials do not appear on the site immediately — visitor sees a “thank you, pending review” confirmation.
Admin-facing functionality
• New submissions land in a “pending” queue in the admin dashboard.
• Admin can approve (publish to homepage/testimonials section), edit, or reject/delete each submission.
• Admin can reorder or unpublish previously approved testimonials at any time.
• Admin receives an email notification when a new testimonial is submitted.
2.3 Careers / Job Postings (Admin-Managed)

Current build status: Fully designed and functionally working on the frontend, including the email-based application flow — but the 5 listed jobs are hardcoded. Applying moves the applicant into their own email app with a pre-filled template addressed to DNL; there is no in-site application form.

Objective: Let DNL publish and take down job openings themselves, with applications continuing to arrive directly in the company inbox — no in-site application form or dashboard inbox required.
User-facing functionality
• Careers page and job detail pages display only currently open roles, pulled live from what admin has published.
• “Apply” continues to open the visitor's email app with a pre-filled subject/body addressed to DNL's careers email (as already built) — no change to this flow.
• “General application” mailto option remains available for roles not currently listed.
Admin-facing functionality
• Admin can create, edit, publish, unpublish, and delete job postings (title, department, type, location, description, requirements).
• Unpublishing/deleting a role removes it from the public careers page immediately.
Notes
• Confirmed: applications are handled entirely through DNL's own email inbox by design — no in-site application form or applicant-tracking dashboard is included in this scope.
2.4 Customer Accounts, Guest Booking & Loyalty Tracking

Current build status: Not yet built — there is currently no account system, and all orders on the live site go through a contact/order form with no way to distinguish returning customers.

Objective: Recognise and track returning customers, without ever forcing a customer to create an account before they can order.
User-facing functionality
• Any visitor can book/order a product as a guest — name, phone/email, and order details only, no account required.
• Visitors can optionally create an account to track their own order history and re-order faster next time.
• Guest orders are matched to an existing customer record where the phone number or email matches a previous order, so repeat guest customers are still recognised internally even without signing up.
Admin-facing functionality
• Admin dashboard flags each order as “new customer” or “returning customer,” based on matched contact details.
• Admin can view a customer list with total orders, first order date, and last order date per customer.
• (For discussion) Whether DNL wants a visible loyalty perk (e.g., a discount after a set number of orders) or just internal visibility into repeat customers for now — this scope currently covers tracking/visibility only, not an automated rewards engine.
2.5 Blog & Product Content Management

Current build status: Blog and product pages are fully designed and live, but content (6 articles, 4 products) is hardcoded into the frontend by the developer.

Objective: Let DNL publish new products and blog articles themselves, without needing a developer for every update.
User-facing functionality
• No change to the visitor-facing blog/product browsing experience — it already works well.
Admin-facing functionality
• Admin can create, edit, publish/unpublish, and delete products — name, category, description, images, origin, available pack sizes, minimum order quantity.
• Admin can create, edit, publish/unpublish, and delete blog articles — title, category, cover image, body content, read-time.
• Changes reflect live on the site immediately, with no redeploy needed.
2.6 Product Booking / Order System

Current build status: The site already has “Place an Order” and “Schedule an Order” entry points, and an order form is referenced (“Open Order Form”) on the contact page — but orders are currently handled fully offline, with no backend, no notification, and no dashboard record.

Objective: Let a customer book/order any product directly from the site, with DNL notified immediately through both email and the admin dashboard — no missed orders.
User-facing functionality
• Customer selects a product (or submits a general enquiry), fills in quantity, delivery location, and contact details, and submits — as a guest or as a logged-in customer (see 2.4).
• Customer sees an on-screen confirmation that their order/enquiry was received; DNL calls or emails to confirm pricing and delivery, consistent with the current site messaging (“No upfront payment — our team will call to confirm”).
Admin-facing functionality
• Every booking triggers an instant email notification to DNL's order inbox with full order details.
• Every booking also appears in real time in the admin dashboard's Orders/Bookings list, with status tracking (New → Confirmed → Fulfilled → Cancelled).
• Admin can update order status and add internal notes per order.
2.7 Easy Contact (Email & WhatsApp)

Current build status: Largely already implemented: a contact form, direct phone/email links, a Google Maps link, a footer WhatsApp link, and a dedicated pre-filled “WhatsApp Us” button all already exist on the live site.

Objective: Keep contact effortless site-wide, and finalise the one remaining piece — persistent floating quick-contact icons.
User-facing functionality
• Visitor can reach DNL by contact form, direct phone call, direct email, or WhatsApp with a pre-filled message — all already present.
Admin-facing functionality
• Add persistent floating “Email” and “WhatsApp” quick-contact icons visible on every page (not just the footer), as originally planned.
• Contact form submissions email straight to DNL's inbox and, optionally, log in the admin dashboard alongside orders/enquiries for a single unified inbox view.

3. Admin Dashboard (Consolidated)

Almost every feature above depends on one shared admin dashboard rather than six separate tools. Below is the consolidated dashboard scope, so it's clear this is one connected system.

• Secure admin login (single admin account).
• Products module — add/edit/remove products and pack sizes.
• Blog module — add/edit/remove articles.
• Careers module — add/edit/remove job postings.
• Testimonials module — approve/reject/edit/reorder submissions.
• Price List module — upload/replace the downloadable price list file.
• Orders/Bookings module — live list of all bookings with status tracking and internal notes.
• Customers module — list of guest and registered customers with order history and new/returning tag.
• Contact/Enquiries module — log of general contact form submissions.
4. Notifications Summary

A quick reference for what triggers a notification, who receives it, and through which channel.

Event
Recipient
Channel
New product booking / order
DNL order inbox + Admin dashboard
Email + Dashboard
New contact form submission
DNL general inbox (+ dashboard log, optional)
Email
New testimonial submitted
Admin dashboard
Email
Job application
DNL careers inbox
Email (via applicant's own email app)
 
5. Assumptions & Out of Scope

Assumptions
• No online payment is required at this stage — all orders/bookings are confirmed offline by phone/email, consistent with the current site.
• Job applications continue to be handled entirely via email (mailto), not an in-site applicant tracking system.
• DNL will supply product data, job listings, and initial blog content to migrate into the new CMS at launch.
Out of scope (unless added later)
• Online payment/checkout integration.
• In-site applicant tracking system or resume upload for careers.
• Automated loyalty rewards engine (points, coupons, tiered discounts) — this scope covers tracking/visibility only.
6. Next Steps

• DNL reviews and confirms this scope, flagging anything to add, remove, or adjust.
• Resolve the two open discussion points: (a) price list — file upload vs. structured data, and (b) whether a loyalty rewards engine is wanted now or later.
• On sign-off, proceed to backend architecture and CMS build against this scope.