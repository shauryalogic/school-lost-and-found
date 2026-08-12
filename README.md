# FoundYou

**A lost-and-found web app for schools — so a parent can find their child's lost item from home.**

🔗 **Live app:** https://found-you.streamlit.app
---

## What it is

When a young child loses something at school, it can be more than just a lost object — a small or anxious child often can't dig through a crowded lost-and-found bin or remember where they left it, and a parent can't always come to school to look.

FoundYou connects **school staff** and **parents**. Staff log found items with a photo in a few seconds; parents search or browse those items from their phone, recognize their child's item, and reserve it for pickup. I designed it with younger children and children with special needs especially in mind.


---

## Screenshots

<!-- Add 2-3 screenshots here so the repo shows the app at a glance.
     Put image files in a /screenshots folder in the repo, then reference them like:
     ![Parent view](screenshots/parent-search.png)
     ![Staff view](screenshots/staff-log.png)
     Use dummy data only - no real student information. -->

*Screenshots coming soon — or try the [live app](https://found-you.streamlit.app).*

---

## What it does

**For parents**
- Search or browse the list of found items, each shown with a photo.
- Reserve an item you recognize as your child's — this tells the school you plan to pick it up and keeps another family from taking it by mistake.

**For staff**
- Log a found item with a photo, name, category, description, and where it was found.
- Manage items with one search box, and move each item through its states: **available → reserved → released**.

---

## How it's built

**Stack**
- **Frontend & app logic:** [Streamlit](https://streamlit.io/) (Python)
- **Database, auth & photo storage:** [Supabase](https://supabase.com/) (PostgreSQL + Storage)
- **Hosting:** Streamlit Community Cloud
- **Dev environment:** GitHub Codespaces

**How the pieces fit together**

```
Browser
   │
   ▼
Streamlit app (Python)
   ├─ streamlit_app.py   →  login + role-based routing
   ├─ views/parent.py    →  search, browse, reserve
   ├─ views/staff.py     →  log items, manage items
   └─ db.py              →  talks to Supabase
   │
   ▼
Supabase
   ├─ Auth          →  parent / staff accounts
   ├─ PostgreSQL    →  items + profiles, protected by Row Level Security
   └─ Storage       →  item photos
```

Every user goes through the Streamlit app, which decides what they can see based on their role. The app never trusts the screen alone to protect data — the database enforces the rules itself (see Privacy below).

---

## Privacy & security

Because FoundYou is about children, protecting their information was a core design decision, not an afterthought. I built the access rules at several layers:

- **Sign-up is gated by a school code.** A stranger can't just create an account and browse a school's found items — you need the school's code to register. I caught this gap myself: at first, anyone could sign up and immediately see everything.
- **Parent search only reads public fields** — item name, description, category, and item number. It never searches the reservation notes, which can contain a child's name.
- **Row Level Security (RLS) in the database** decides who can read what. A parent can only load items that are *available* or that *they personally reserved*; staff can see everything. Even if the code asked for more, the database returns only what that user is allowed to see.
- **Roles are enforced server-side.** A database trigger assigns new sign-ups the `parent` role, and a SQL helper (`is_staff()`) checks staff access.
- **API keys are never committed.** The app's Supabase keys are stored as secrets, not in the code, so they stay out of the public repo.

The lesson I took from this: hiding something on the screen isn't the same as protecting it — real security has to be enforced underneath.

---

## The data model (items table)

Each found item is one row in an `items` table:

| Field | Type | What it's for |
|---|---|---|
| `id` | `uuid` | Internal unique ID (primary key) |
| `item_number` | `int8` | Human-friendly ID shown to staff and parents |
| `name` | `text` | The item's name |
| `category` | `text` | What kind of item it is |
| `description` | `text` | More detail about the item |
| `location_found` | `text` | Where it was found |
| `photo_url` | `text` | Link to the item's photo in Supabase Storage |
| `status` | `text` | `available` -> `reserved` -> `released` |
| `date_found` | `date` | When it was logged |
| `created_at` | `timestamptz` | When the row was created |
| `reservation_comments` | `text` | Who it's being held for (staff-only; kept private) |
| `reserved_by` | `uuid` | The parent who reserved it |
| `reservation_date` | `date` | When it was reserved |
| `released_date` | `date` | When it was handed back to the family |

---

## Testing

I tested FoundYou with a written test plan of **50+ cases across desktop and phone**, covering the full flow — logging, searching, reserving, releasing, permissions, and validation. I found and fixed real issues along the way, including a form that cleared itself on a validation error and improvements to how the app works on phones.

---

## Roadmap (v2.0)

Features I deliberately kept out of v1 so the core app would be reliable, and would build next:

- **Notifications** — email/text alerts when a matching item is logged, or when a reserved item is ready.
- **Automatic item entry** — use AI to read the uploaded photo and suggest the item's name and category.
- **Individual staff accounts** — for accountability (v1 uses a shared staff account).
- **Multi-school support** — a `school_id` is already stored on profiles to make this possible.

---

## About

Built by **Shaurya** 
FoundYou is my first real-world project — turning a frustrating experience I remembered from childhood into something that could help the next kid.
