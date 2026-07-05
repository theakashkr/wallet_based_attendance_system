# 🛡️ WalletGuard — Wallet-Based Attendance & Access Control System

A Django web application that tracks employee office attendance, calculates stay duration, and deducts credits from a virtual wallet. Users with insufficient credits are denied entry. Features **QR Code scan verification** for secure check-in/check-out.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **💳 Virtual Wallet** — Each user has a credit balance (new users get 100 credits)
- **🔓 Check-In / Check-Out** — Records entry/exit times with credit deduction (₹0.10/min)
- **📷 QR Code Verification** — Time-rotating QR codes (30s) must be scanned to check in/out
- **🚫 Access Control** — Users with ≤ 0 balance are denied entry
- **💰 Wallet Recharge** — Add credits with quick-select amounts (₹50, ₹100, ₹200, ₹500)
- **📋 Attendance History** — Full log of all visits with duration and credits deducted
- **🔄 Transaction History** — Complete recharge log
- **🎨 Modern Dark UI** — Glassmorphism design, smooth animations, fully responsive
- **🔐 Authentication** — Login, registration, and session management

---

## 🏗️ Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.10+ / Django 5.x          |
| Frontend   | HTML5, Vanilla CSS, Vanilla JS      |
| Database   | PostgreSQL (configurable to MySQL)  |
| QR Scanner | html5-qrcode (CDN)                 |
| QR Generator | Python `qrcode` library           |

---

## 📁 Project Structure

```
├── manage.py
├── requirements.txt
├── wallet_attendance/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── attendance/                 # Main app
    ├── models.py               # UserProfile, Attendance, Transaction
    ├── views.py                # Dashboard, Check-in/out, Recharge, QR endpoints
    ├── urls.py                 # URL routing
    ├── qr_utils.py             # HMAC token generation & QR image rendering
    ├── admin.py
    ├── forms.py
    ├── templatetags/
    ├── static/attendance/
    │   ├── css/style.css       # Complete design system
    │   └── js/dashboard.js     # QR scanner + AJAX logic
    └── templates/attendance/
        ├── base.html
        ├── login.html
        ├── register.html
        ├── dashboard.html      # Main dashboard with QR scanner modal
        └── qr_display.html     # Admin QR display page
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/WalletGuard.git
cd WalletGuard
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the database

**PostgreSQL** (default):
```sql
CREATE DATABASE wallet_attendance_db;
```

Update credentials in `wallet_attendance/settings.py`:
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "wallet_attendance_db",
        "USER": "postgres",
        "PASSWORD": "your_password",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}
```

### 5. Run migrations

```bash
python manage.py makemigrations attendance
python manage.py migrate
```

### 6. Create a superuser (for admin / QR display)

```bash
python manage.py createsuperuser
```

### 7. Start the server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** 🎉

---

## 📷 QR Code Verification Flow

1. **Admin** opens `/qr-display/` on an office monitor — shows a rotating QR code (refreshes every 30s)
2. **Employee** clicks "Scan & Check In" on their dashboard — camera opens
3. **Employee** scans the QR code from the office monitor
4. **Server** validates the HMAC token → records attendance

> The QR tokens use **HMAC-SHA256** with a 30-second time window. No extra database table needed — fully stateless.

---

## 💡 Business Logic

| Action     | Rule                                                  |
|------------|-------------------------------------------------------|
| Check-In   | Wallet balance must be > 0; valid QR code required    |
| Check-Out  | Duration calculated; credits deducted at ₹0.10/minute |
| Recharge   | Any positive amount; logged as a Transaction           |
| New User   | Starts with 100 free credits                           |

---

## 🔗 Available URLs

| URL             | Access     | Description              |
|-----------------|------------|--------------------------|
| `/`             | Logged in  | Main dashboard           |
| `/qr-display/`  | Admin only | QR code for office screen |
| `/admin/`       | Admin only | Django admin panel       |
| `/login/`       | Public     | Login page               |
| `/register/`    | Public     | Registration page        |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
