# MaraGate System — Installation & Deployment Guide
## Maasai Mara Ecosystem Management & Safari Gate Clearance System
### Narok County Government

---

## Prerequisites

| Requirement | Version | Download |
|-------------|---------|----------|
| Python | 3.12+ | https://www.python.org/downloads/ |
| MySQL | 8.0+ | https://dev.mysql.com/downloads/installer/ |
| Git | Any | https://git-scm.com/ |

---

## Quick Start (Windows)

### Step 1 — Install MySQL
1. Download **MySQL Installer** from https://dev.mysql.com/downloads/installer/
2. Choose **Developer Default** setup
3. Set a root password you'll remember
4. Start **MySQL 8.0** service

### Step 2 — Create the Database
Open **MySQL Workbench** or **MySQL Command Line Client** and run:

```sql
CREATE DATABASE maasai_mara_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 3 — Clone / Extract the Project
```
maasai_mara_system\
├── app\
│   ├── __init__.py
│   ├── models\
│   ├── routes\
│   ├── utils\
│   ├── static\
│   └── templates\
├── migrations\
│   ├── schema.sql
│   └── seed_data.sql
├── config.py
├── run.py
├── init_db.py
├── requirements.txt
├── .env.example
├── setup.bat
└── run_app.bat
```

### Step 4 — Configure Environment
Copy `.env.example` to `.env` and edit:

```env
SECRET_KEY=your-strong-random-secret-key-here
DB_HOST=localhost
DB_PORT=3306
DB_NAME=maasai_mara_db
DB_USER=root
DB_PASSWORD=your_mysql_root_password
```

> **Security:** Change `SECRET_KEY` to a random 50+ character string in production.

### Step 5 — Run Setup (Automated)
Double-click **`setup.bat`** or run in Command Prompt:

```bat
setup.bat
```

This will:
- Create a Python virtual environment
- Install all packages from `requirements.txt`
- Initialize the database tables
- Seed sample data

### Step 6 — Start the Application
```bat
run_app.bat
```

Open browser: **http://localhost:5000**

---

## Manual Installation

```bat
:: Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt

:: Set environment
copy .env.example .env
:: Edit .env with your MySQL credentials

:: Initialize database
python init_db.py

:: Run the app
python run.py
```

---

## Default Login Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin (County Official)** | admin@maranaorok.go.ke | Admin@2024 |
| **Tour Guide** | guide@example.com | Guide@2024 |
| **Tour Guide 2** | mary@safarico.co.ke | Guide@2024 |

> **Important:** Change all passwords after first login in production.

---

## System Architecture

```
Browser
   │
   ▼
Flask Application (run.py)
   │
   ├── /                 → Auth (login, register, profile)
   ├── /admin/*          → Admin Blueprint
   │   ├── /dashboard    → Analytics & stats
   │   ├── /users        → User management
   │   ├── /clearances   → Gate clearance approval
   │   ├── /revenue      → Revenue monitoring
   │   ├── /vehicles     → Vehicle density
   │   ├── /wildlife     → Wildlife tracking map
   │   ├── /reports      → PDF & Excel reports
   │   └── /alerts       → System alerts
   │
   ├── /guide/*          → Guide Blueprint
   │   ├── /dashboard    → Guide home
   │   ├── /vehicles     → Vehicle management
   │   ├── /clearances   → Request & view clearances
   │   └── /sightings    → Wildlife reporting
   │
   └── /api/v1/*         → REST API
       ├── /wildlife/map → Map data (JSON)
       ├── /gates/density → Gate counts
       ├── /clearance/<token>/status → QR verify
       └── /dashboard/stats → Live stats
           │
           ▼
        MySQL Database (maasai_mara_db)
```

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `users` | Admins and tour guides |
| `vehicles` | Registered safari vehicles |
| `gate_clearances` | Clearance requests & approvals |
| `passengers` | Passenger manifests |
| `wildlife_sightings` | GPS wildlife reports |
| `sighting_photos` | Uploaded wildlife photos |
| `revenue_records` | Fee collection records |
| `alerts` | System-wide announcements |
| `audit_logs` | Full activity trail |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/wildlife/map` | Wildlife sightings GeoJSON |
| GET | `/api/v1/gates/density` | Today's vehicle counts by gate |
| GET | `/api/v1/clearance/<token>/status` | Verify clearance by QR token |
| GET | `/api/v1/dashboard/stats` | Live system statistics |
| GET | `/api/v1/revenue/chart` | Revenue chart data |
| GET | `/api/v1/alerts/active` | Active system alerts |

---

## Key Features

### Admin Portal
- **Dashboard**: Real-time charts (Chart.js), pending approvals badge
- **User Management**: Create/suspend/verify guides, export PDF
- **Gate Clearances**: Filter by gate/status/date, approve/reject with notes
- **Revenue Monitoring**: Daily line chart, revenue by gate, transaction log
- **Vehicle Density**: Hourly bar chart, today's entries per gate
- **Wildlife Tracking**: Leaflet.js interactive map, color-coded by species, species totals
- **Reports**: PDF (ReportLab) and Excel (openpyxl) generation
- **Alerts**: Publish warnings visible to all guides
- **Audit Logs**: Full immutable activity trail

### Guide Portal
- **Dashboard**: Quick stats, recent clearances, system alerts
- **Vehicle Registration**: Multi-vehicle support, insurance tracking
- **Gate Clearance Request**: Inline passenger manifest builder, fee estimator
- **QR Code Token**: Auto-generated on submission, downloadable PNG
- **Wildlife Sighting**: GPS via device or map click, Leaflet pick-point map, photo upload
- **Clearance History**: Full history with status tracking

---

## File Upload Storage

Uploaded files are stored under `app/static/uploads/`:

```
uploads/
├── qrcodes/        ← Gate clearance QR codes (.png)
├── photos/         ← Wildlife sighting photos
└── manifests/      ← Passenger manifest files
```

---

## Production Deployment (Windows Server)

### Using Waitress (recommended for Windows)
```bat
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 run:app
```

### Using IIS with wfastcgi
1. Install IIS and Python wfastcgi
2. Configure `web.config`:
```xml
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI"
           path="*"
           verb="*"
           modules="FastCgiModule"
           scriptProcessor="C:\path\to\python.exe|C:\path\to\wfastcgi.py"
           resourceType="Unspecified"
           requireAccess="Script" />
    </handlers>
  </system.webServer>
  <appSettings>
    <add key="WSGI_HANDLER" value="run.app" />
    <add key="WSGI_LOG" value="C:\logs\wfastcgi.log" />
  </appSettings>
</configuration>
```

---

## Security Checklist (Before Go-Live)

- [ ] Change `SECRET_KEY` in `.env` to a strong random value
- [ ] Change all default passwords
- [ ] Set `FLASK_ENV=production` in `.env`
- [ ] Enable HTTPS (SSL certificate)
- [ ] Restrict MySQL to localhost only
- [ ] Set up regular database backups
- [ ] Configure upload directory permissions
- [ ] Set up firewall rules (port 80/443 only)

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in activated venv |
| `Access denied for user 'root'` | Check `DB_PASSWORD` in `.env` |
| `Unknown database` | Create DB: `CREATE DATABASE maasai_mara_db;` |
| `Port 5000 already in use` | Change port: `python run.py` → edit `run.py` port |
| QR codes not showing | Check `app/static/uploads/qrcodes/` exists and is writable |
| Map not loading | Check internet connection (Leaflet/OpenStreetMap CDN) |

---

## Support

**System:** Maasai Mara Ecosystem Management & Safari Gate Clearance System  
**County:** Narok County Government, Kenya  
**Tech Stack:** Python 3.12 · Flask 3.0 · MySQL 8.0 · Bootstrap 5 · Leaflet.js · Chart.js
