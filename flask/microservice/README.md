# Crust & Co. — microservices version

The same pizza shop as `../monolith-app`, split into five services and started with Docker Compose.

## Run it

```bash
cp .env.example .env        # then change SECRET_KEY and the passwords
docker compose up --build
```

Open http://localhost:5000 (change `WEB_PORT` in `.env` to use another port).
Logins from the sample data: `admin@demo.com` / `123456` (admin), `demo@demo.com` / `123456` (customer).

`docker compose ps` should list all six containers as `healthy`. Logs: `docker compose logs -f order-service`.

The database is loaded from `db/init/01-pizza.sql` **only on the first start**, while the `db_data` volume is empty.
To start again from the sample data: `docker compose down -v && docker compose up --build`.

## Services

```
browser ──► web :5000 ──┬──► user-service     users
                        ├──► menu-service     menu_items
                        ├──► order-service ──► menu-service (prices at checkout)
                        │                     orders, order_items, order_status_history
                        └──► message-service  messages
                                   all ──► db (MySQL 8.4, database `pizza`)
```

| Service | Folder | Owns tables | Main endpoints |
|---|---|---|---|
| web | `web/` | none (no DB access) | every page of the shop and admin; keeps the login session |
| user-service | `services/user-service/` | `users` | `POST /auth/login`, `POST /users`, `GET /users[?ids=]`, `GET /users/<id>` |
| menu-service | `services/menu-service/` | `menu_items` | `GET /items[?ids=]`, `GET/PUT/DELETE /items/<id>`, `POST /items`, `PATCH /items/<id>/availability`, `GET /meta` |
| order-service | `services/order-service/` | `orders`, `order_items`, `order_status_history` | `GET/POST /orders`, `GET /orders/<id>`, `POST /orders/<id>/status`, `GET /orders/pending-count`, `GET /orders/stats/today`, `GET /reports/revenue` |
| message-service | `services/message-service/` | `messages` | `POST /messages`, `GET /messages?page=` |
| db | image `mysql:8.4` | — | — |

Rules the code follows:

- All services share one database, but a service only reads and writes the tables it owns. When it needs data from another service's tables it calls that service (for example, order-service asks menu-service for prices; web asks user-service for the names in an order's history).
- Only `web` is published to your machine. The APIs and MySQL are reachable only on the internal `backend` network, so the APIs trust the `user_id` that web sends them.
- Validation lives in the API services; web shows their `{"error": ...}` messages in the same places as before.
- Every API service has `GET /health` (checks the database). Compose uses it so web starts only after the APIs are ready.
- `common/` (database helper, JSON encoding, phone check) is copied into each API image.

## Run without Docker (development)

With MySQL running locally and the `pizza` database loaded:

```bash
pip install Flask mysql-connector-python requests
export PYTHONPATH=$PWD                     # so the services find common/
(cd services/user-service    && flask --app app run -p 5001) &
(cd services/menu-service    && flask --app app run -p 5002) &
(cd services/order-service   && flask --app app run -p 5003) &
(cd services/message-service && flask --app app run -p 5004) &
(cd web && flask --app app run -p 5000)
```

The default service URLs in `web/api.py` and `services/order-service/app.py` already point at these ports.
