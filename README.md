# Tradexa

A Django-based warehouse **shipping-box recommendation system**. Add products
to a cart and Tradexa recommends the cheapest shipping box that fits the order
by volume (with an 80% packing-efficiency factor) and weight.

## Tech stack

- **Backend:** Django 4.2 + Django REST Framework
- **Database:** Supabase (PostgreSQL) via `dj-database-url` (falls back to
  SQLite locally when `DATABASE_URL` is unset)
- **Auth:** Supabase Auth (JWT) validated with `djangorestframework-simplejwt`
  (endpoints currently use `AllowAny` so they can be tested without auth)
- **Frontend:** Vanilla JS + HTML/CSS served through a Django template, styled
  with the Tailwind CDN
- **Env management:** `python-dotenv`

## Project layout

```
tradexa/
├── manage.py
├── requirements.txt
├── .env.example
├── seed_data/             # products.json, boxes.json fixtures
├── tradexa/               # settings, urls, wsgi
├── inventory/             # Product, Box — models, API, admin, seed command
├── orders/                # Order, OrderItem, BoxRecommendation
│   └── services/          # packing_calculator.py, box_selector.py
└── templates/dashboard/   # index.html — single-page UI
```

## Setup

1. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set at least `SECRET_KEY`. Leave `DATABASE_URL` unset to use
   a local SQLite database, or set it to connect to Supabase (see below).

4. **Migrate and seed**

   ```bash
   python manage.py migrate
   python manage.py seed_tradexa
   ```

   `seed_tradexa` clears existing products/boxes and loads 8 products and 4
   boxes from `seed_data/`.

5. **(Optional) create an admin user**

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the server**

   ```bash
   python manage.py runserver
   ```

   - Dashboard: <http://127.0.0.1:8000/>
   - Django admin: <http://127.0.0.1:8000/admin/>

## Connecting Supabase

1. In your Supabase project go to **Project Settings → Database** and copy the
   connection string (URI). It looks like:

   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.<project-ref>.supabase.co:5432/postgres
   ```

2. Put it in `.env` as `DATABASE_URL` and also set `SUPABASE_URL` /
   `SUPABASE_ANON_KEY` (from **Project Settings → API**):

   ```
   DATABASE_URL=postgresql://postgres:your-password@db.your-ref.supabase.co:5432/postgres
   SUPABASE_URL=https://your-ref.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   ```

   SSL is required and is enabled automatically when `DATABASE_URL` is present.

3. Re-run migrations and seeding against Supabase:

   ```bash
   python manage.py migrate
   python manage.py seed_tradexa
   ```

## API reference

All endpoints are prefixed with `/api/`.

| Method | Path                          | Description                                   |
| ------ | ----------------------------- | --------------------------------------------- |
| GET    | `/api/products/`              | List all products                             |
| GET    | `/api/products/<id>/`         | Product detail                                |
| GET    | `/api/boxes/`                 | List all active boxes                         |
| POST   | `/api/orders/`                | Create an order with items + recommendation   |
| GET    | `/api/orders/<id>/`           | Order detail with recommendation              |
| POST   | `/api/orders/<id>/recommend/` | (Re)compute the recommendation for an order   |
| POST   | `/api/recommend/preview/`     | Preview a recommendation without saving        |

**Create order / preview body**

```json
{ "items": [ { "product_id": 1, "quantity": 2 } ] }
```

The preview response also includes a `boxes` array where every active box is
flagged with `fits` and `is_recommended`, which the dashboard uses to grey out
boxes that are too small.

## Recommendation logic

- `orders/services/packing_calculator.py` — sums item volume and weight and
  divides volume by the **0.8 packing-efficiency factor** to get an effective
  volume.
- `orders/services/box_selector.py` — keeps active boxes whose internal volume
  ≥ effective volume and whose weight limit ≥ total weight, then returns the
  **cheapest** one. If none fit it returns
  `"No suitable box — consider splitting the order"`.
