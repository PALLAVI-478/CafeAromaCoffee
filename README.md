# Café Aroma.coffee

A polished Flask + SQLite café ordering website with customer and owner areas.

## Features
- Responsive café homepage, About, Menu and Contact pages
- Customer registration/login/account
- Menu browsing and category filters
- Cart with quantity controls
- Checkout and order tracking
- Owner dashboard with statistics
- Owner menu management
- Owner order status management
- Local SVG artwork included in `static/images`

## Run locally
```bash
python -m venv venv
# Windows
venv\Scripts\activate
pip install -r requirements.txt
python database.py
python app.py
```
Open `http://127.0.0.1:5000`.

## Owner login (local demo)
Email: `owner@cafe.com`
Password: `owner123`

Before public deployment, set `SECRET_KEY`, `OWNER_EMAIL`, and `OWNER_PASSWORD` as environment variables.

## Deployment note
`cafe.db` is intentionally ignored by Git. SQLite data on many free hosting services is not persistent. For a real public multi-user café, use a persistent database such as PostgreSQL.

## Visual design
The homepage uses real café photography from Unsplash and a public-domain café interior image from Wikimedia Commons. The Wikimedia image is the Drew Coffman photo documented as CC0 on its Commons file page. Unsplash photos are loaded from their image CDN so the project remains lightweight.
