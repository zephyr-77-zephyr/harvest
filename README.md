# Harvest Helper

Harvest Helper is a full-stack Django + Django REST Framework marketplace for ordering fruits, vegetables, and other farm goods. It blends Lazada/Shopee-style shopping with farmer-friendly tools, Tailwind-powered UI, and responsive templates.

## Features

- Authentication with signup, login, logout, and password reset (console email backend).
- Buyer and seller roles; sellers manage inventory and see sales metrics.
- Categories, product search, price filters, featured items, and responsive cards.
- Cart, checkout, order history, and order tracking statuses.
- Ratings and reviews per product.
- REST API endpoints for products, categories, and authenticated order history.
- Admin tools to manage users, products, orders, carts, and reviews.

## Tech Stack

- Django 5, Django REST Framework, SQLite (default, swap for PostgreSQL in production).
- Tailwind CSS via CDN for styling.
- HTML templates rendered server-side.

## Getting Started

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt  # or pip install django djangorestframework pillow
python manage.py migrate
python manage.py createsuperuser  # optional, for admin
python manage.py runserver
```

Visit http://127.0.0.1:8000 to browse the storefront. Access the admin panel at http://127.0.0.1:8000/admin.

## Tailwind Palette

- Leaf Green `#6BB42F`
- Rich Soil Brown `#7B4B28`
- Harvest Orange `#D97A2B`

## Deployment on Render

### Prerequisites
- GitHub repository with your code
- Render account (free tier available)

### Setup Steps

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial deployment setup"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy on Render**:
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect your `render.yaml` configuration
   - Click "Create Web Service"

3. **Environment Variables** (Render will set these automatically):
   - `DEBUG`: false
   - `SECRET_KEY`: Auto-generated
   - `DATABASE_URL`: Auto-generated PostgreSQL connection string

4. **Post-Deployment**:
   - Create a superuser for admin access:
     ```bash
     # In Render dashboard, go to your service → Shell
     python manage.py createsuperuser
     ```

### Local Development

For local development with SQLite (default):
1. Copy `.env.example` to `.env` and adjust if needed
2. Run migrations: `python manage.py migrate`
3. Create superuser: `python manage.py createsuperuser`
4. Start server: `python manage.py runserver`

### Production vs Development

- **Production**: PostgreSQL database, DEBUG=False, static files served via Whitenoise
- **Development**: SQLite database, DEBUG=True, local static files

The app automatically detects the environment and adjusts database configuration accordingly.

