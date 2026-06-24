# Tradexa

A Django-based warehouse **shipping-box recommendation system**. Add products
to a cart and Tradexa recommends the cheapest shipping box that fits the order
by volume (with an 80% packing-efficiency factor) and weight.

## Tech stack

- **Backend:** Django 4.2 + Django REST Framework
- **Database:** PostgreSQL via `dj-database-url` (falls back to SQLite locally
  when `DATABASE_URL` is unset). SSL is required for remote hosts and disabled
  automatically for `localhost`/`127.0.0.1`.
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

   Edit `.env` and set `SECRET_KEY` and `DATABASE_URL` for your local Postgres
   (see below). Leave `DATABASE_URL` unset to fall back to a local SQLite
   database instead.

4. **Create the local PostgreSQL database** (skip if using SQLite)

   With PostgreSQL installed and running, create the `tradexa` database:

   ```bash
   psql -U postgres -c "CREATE DATABASE tradexa;"
   ```

   Then set the matching URL in `.env`:

   ```
   DATABASE_URL=postgresql://postgres:your-password@localhost:5432/tradexa
   ```

5. **Migrate and seed**

   ```bash
   python manage.py migrate
   python manage.py seed_tradexa
   ```

   `seed_tradexa` clears existing products/boxes and loads 8 products and 4
   boxes from `seed_data/`.

6. **(Optional) create an admin user**

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the server**

   ```bash
   python manage.py runserver
   ```

   - Dashboard: <http://127.0.0.1:8000/>
   - Django admin: <http://127.0.0.1:8000/admin/>

## Using a remote PostgreSQL (e.g. Supabase)

Point `DATABASE_URL` at the remote connection string — SSL is enabled
automatically for any non-`localhost` host:

```
DATABASE_URL=postgresql://postgres:your-password@db.your-ref.supabase.co:5432/postgres
```

If your password contains URL-special characters (`@ : / # ? %`), URL-encode
them (e.g. `@` → `%40`). Then re-run `migrate` and `seed_tradexa`.

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
