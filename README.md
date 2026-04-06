# Nails by Shreya — Flask Backend

## Project Structure
```
nbs_backend/
├── app.py                  # Main Flask app
├── requirements.txt
├── templates/
│   ├── index.html          # Your frontend (integrated)
│   ├── admin_login.html    # Admin login page
│   └── admin.html          # Admin dashboard
└── instance/
    └── nbs.db              # SQLite database (auto-created)
```

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
- **Website:** http://localhost:5000
- **Admin Panel:** http://localhost:5000/admin

## Admin Login
- **URL:** `/admin/login`
- **Default password:** `shreya123`
- To change: edit `ADMIN_PASSWORD` in `app.py`

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/book` | Submit a booking |
| POST | `/api/contact` | Submit a contact message |
| GET | `/api/blocked-dates` | Get all blocked dates |

## Admin Features
- ✅ View all bookings
- ✅ Confirm / Cancel bookings
- ✅ WhatsApp reply to clients directly
- ✅ View & mark messages as read
- ✅ Block / unblock dates
- ✅ Stats dashboard

## Deploying (Free)
- **Render.com** → Push to GitHub → Connect repo → Set start command: `python app.py`
- **Railway.app** → Same process, even easier

## Notes
- Images (`.heic`, `.jpg`) and video must be in the same folder as `index.html`
  when running locally, or hosted on a CDN/GitHub for production.
- WhatsApp notifications work by opening a `wa.me` link in a new tab —
  no API key needed.
