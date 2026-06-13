# AI Colorization Full-Stack Project

This project contains a complete backend and frontend structure for an image colorization website.

## Stack
- Backend: Flask, SQLAlchemy, JWT, CORS
- Database: SQLite by default (easy local run). Swap to PostgreSQL with `DATABASE_URL`
- Frontend: HTML, CSS, Vanilla JavaScript
- Inference: PyTorch + segmentation_models_pytorch

## Features
- Register / login / password reset token flow
- Upload grayscale image to backend
- Backend runs the colorization model
- Saves original and output images
- Stores user info, image info, feedback, preferences, password reset tokens, and activity logs
- User history page
- Admin dashboard with real backend stats

## Project structure

```text
colorization_fullstack/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── extensions.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── static/
│   │   ├── originals/
│   │   └── outputs/
│   └── instance/
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── README.md
```

## How to run

### 1) Put your checkpoint in the backend folder
Expected path by default:

```text
backend/colorization_best.pth
```

Or set a custom path:

```bash
export MODEL_CHECKPOINT=/full/path/to/colorization_best.pth
```

### 2) Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install requirements

```bash
pip install -r backend/requirements.txt
```

### 4) Run the app
From the parent folder that contains `colorization_fullstack`:

```bash
python -m backend.app
```

Or from inside the project folder:

```bash
python -m backend.app
```

The app runs on:

```text
http://127.0.0.1:5000
```

## Default seeded admin
If the database is empty, the app seeds:

- Email: `admin@example.com`
- Password: `admin123`

## Notes
- SQLite is used by default so the project works immediately.
- To use PostgreSQL instead, set `DATABASE_URL`.
- The current model service preserves your uploaded inference logic as closely as possible.
- If `segmentation_models_pytorch` is not installed or the checkpoint is missing, the app falls back to a grayscale passthrough image so the rest of the app still runs.

## Main API routes

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`

### Users
- `GET /api/users/me`
- `PUT /api/users/me`
- `PUT /api/users/preferences`
- `PUT /api/users/change-password`

### Images
- `POST /api/images/upload`
- `GET /api/images/my-history`
- `GET /api/images/<id>`
- `DELETE /api/images/<id>`

### Feedback
- `POST /api/feedback`
- `GET /api/feedback/me`

### Admin
- `GET /api/admin/stats`
- `GET /api/admin/users`
- `GET /api/admin/images`
- `GET /api/admin/feedback`
- `GET /api/admin/activity`
