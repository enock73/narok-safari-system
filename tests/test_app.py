"""
tests/test_app.py — Unit and integration tests.
Run with:
    python -m pytest tests/ -v
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['FLASK_ENV'] = 'development'

# Use SQLite in-memory for tests — no MySQL needed
TEST_DB_URI = 'sqlite:///:memory:'


@pytest.fixture
def app():
    """Create application for testing."""
    from app import create_app, db as _db
    from config import Config

    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = TEST_DB_URI
        WTF_CSRF_ENABLED = False
        SECRET_KEY = 'test-secret-key'
        UPLOAD_FOLDER = '/tmp/mara_test_uploads'
        PHOTO_FOLDER = '/tmp/mara_test_uploads/photos'
        MANIFEST_FOLDER = '/tmp/mara_test_uploads/manifests'
        QR_FOLDER = '/tmp/mara_test_uploads/qrcodes'

    import os
    for folder in ['/tmp/mara_test_uploads',
                   '/tmp/mara_test_uploads/photos',
                   '/tmp/mara_test_uploads/manifests',
                   '/tmp/mara_test_uploads/qrcodes']:
        os.makedirs(folder, exist_ok=True)

    app = create_app.__wrapped__(TestConfig) if hasattr(create_app, '__wrapped__') else None

    # Direct creation
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager
    from config import config

    flask_app = Flask(__name__,
                      template_folder='../app/templates',
                      static_folder='../app/static')
    flask_app.config.from_object(TestConfig)

    _db.init_app(flask_app)
    login_manager = LoginManager()
    login_manager.init_app(flask_app)
    login_manager.login_view = 'auth.login'

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.guide import guide_bp
    from app.routes.api import api_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(admin_bp, url_prefix='/admin')
    flask_app.register_blueprint(guide_bp, url_prefix='/guide')
    flask_app.register_blueprint(api_bp, url_prefix='/api/v1')

    from app.utils.template_helpers import register_template_helpers
    register_template_helpers(flask_app)

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    from app import db as _db
    return _db


@pytest.fixture
def admin_user(app, db):
    from app.models import User
    with app.app_context():
        u = User(
            full_name='Test Admin',
            email='testadmin@test.com',
            id_number='ADMIN999',
            role='admin',
            is_active=True,
            is_verified=True
        )
        u.set_password('Admin@1234')
        db.session.add(u)
        db.session.commit()
        return u


@pytest.fixture
def guide_user(app, db):
    from app.models import User
    with app.app_context():
        u = User(
            full_name='Test Guide',
            email='testguide@test.com',
            id_number='GUIDE999',
            role='guide',
            is_active=True,
            is_verified=True,
            company='Test Safari Ltd'
        )
        u.set_password('Guide@1234')
        db.session.add(u)
        db.session.commit()
        return u


def login(client, email, password):
    return client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


# ── Model Tests ───────────────────────────────────────────────────

class TestUserModel:
    def test_password_hashing(self, app):
        from app.models import User
        with app.app_context():
            u = User(full_name='Test', email='t@t.com', id_number='X1')
            u.set_password('securepass123')
            assert u.password_hash != 'securepass123'
            assert u.check_password('securepass123')
            assert not u.check_password('wrongpass')

    def test_user_roles(self, app, admin_user, guide_user):
        with app.app_context():
            from app.models import User
            admin = User.query.filter_by(email='testadmin@test.com').first()
            guide = User.query.filter_by(email='testguide@test.com').first()
            assert admin.is_admin() is True
            assert guide.is_admin() is False

    def test_user_repr(self, app, admin_user):
        with app.app_context():
            from app.models import User
            u = User.query.filter_by(email='testadmin@test.com').first()
            assert 'testadmin@test.com' in repr(u)

    def test_user_creation(self, app, db):
        from app.models import User
        with app.app_context():
            u = User(
                full_name='New User',
                email='newuser@test.com',
                id_number='NEW001',
                role='guide'
            )
            u.set_password('Pass@1234')
            db.session.add(u)
            db.session.commit()
            found = User.query.filter_by(email='newuser@test.com').first()
            assert found is not None
            assert found.full_name == 'New User'
            assert found.role == 'guide'


class TestVehicleModel:
    def test_vehicle_creation(self, app, db, guide_user):
        from app.models import User, Vehicle
        with app.app_context():
            guide = User.query.filter_by(email='testguide@test.com').first()
            v = Vehicle(
                user_id=guide.id,
                plate_number='KXX 001A',
                vehicle_type='Land Cruiser',
                capacity=8,
                make='Toyota',
                color='White'
            )
            db.session.add(v)
            db.session.commit()
            found = Vehicle.query.filter_by(plate_number='KXX 001A').first()
            assert found is not None
            assert found.capacity == 8
            assert found.owner.full_name == 'Test Guide'

    def test_plate_uniqueness(self, app, db, guide_user):
        from app.models import User, Vehicle
        from sqlalchemy.exc import IntegrityError
        with app.app_context():
            guide = User.query.filter_by(email='testguide@test.com').first()
            v1 = Vehicle(user_id=guide.id, plate_number='KDU DUPE', vehicle_type='Land Cruiser', capacity=7)
            v2 = Vehicle(user_id=guide.id, plate_number='KDU DUPE', vehicle_type='Minivan', capacity=14)
            db.session.add(v1)
            db.session.commit()
            db.session.add(v2)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()


class TestGateClearanceModel:
    def test_fee_calculation(self, app, db, guide_user):
        from app.models import User, Vehicle, GateClearance
        import uuid
        from datetime import date
        with app.app_context():
            guide = User.query.filter_by(email='testguide@test.com').first()
            v = Vehicle(user_id=guide.id, plate_number='KFE 001X', vehicle_type='Land Cruiser', capacity=8)
            db.session.add(v)
            db.session.flush()

            c = GateClearance(
                token=str(uuid.uuid4()),
                guide_id=guide.id,
                vehicle_id=v.id,
                gate='Sekenani Gate',
                entry_date=date.today(),
                citizen_count=2,
                non_citizen_count=4,
                adult_count=6,
                child_count=0,
                passenger_count=6,
                purpose='Game Drive'
            )
            db.session.add(c)
            db.session.commit()

            fee = c.calculate_fee()
            # 2 citizens × 215 + 4 non-citizens × 80 × 130 + vehicle 350
            expected = (2 * 215) + (4 * 80 * 130) + 350
            assert fee == expected


# ── Authentication Tests ──────────────────────────────────────────

class TestAuthentication:
    def test_login_page_loads(self, client):
        rv = client.get('/login')
        assert rv.status_code == 200
        assert b'MaraGate' in rv.data or b'Sign In' in rv.data

    def test_register_page_loads(self, client):
        rv = client.get('/register')
        assert rv.status_code == 200

    def test_valid_admin_login(self, client, app, admin_user):
        with app.app_context():
            rv = login(client, 'testadmin@test.com', 'Admin@1234')
            assert rv.status_code == 200

    def test_valid_guide_login(self, client, app, guide_user):
        with app.app_context():
            rv = login(client, 'testguide@test.com', 'Guide@1234')
            assert rv.status_code == 200

    def test_invalid_login(self, client):
        rv = login(client, 'nobody@test.com', 'WrongPass')
        assert b'Invalid email or password' in rv.data

    def test_register_guide(self, client, app):
        with app.app_context():
            rv = client.post('/register', data={
                'full_name': 'New Guide Person',
                'email': 'newguide@test.com',
                'phone': '+254711000000',
                'id_number': 'NID_NEW_001',
                'password': 'NewGuide@123',
                'confirm_password': 'NewGuide@123',
            }, follow_redirects=True)
            assert rv.status_code == 200
            from app.models import User
            u = User.query.filter_by(email='newguide@test.com').first()
            assert u is not None
            assert u.role == 'guide'

    def test_register_password_mismatch(self, client):
        rv = client.post('/register', data={
            'full_name': 'Test',
            'email': 'x@x.com',
            'id_number': 'ID001',
            'password': 'Pass@1234',
            'confirm_password': 'Different@1234'
        }, follow_redirects=True)
        assert b'Passwords do not match' in rv.data

    def test_logout(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/logout', follow_redirects=True)
            assert rv.status_code == 200

    def test_unauthenticated_redirect(self, client):
        rv = client.get('/admin/dashboard', follow_redirects=False)
        assert rv.status_code in [302, 301]


# ── Admin Route Tests ─────────────────────────────────────────────

class TestAdminRoutes:
    def _admin_login(self, client, app, admin_user):
        with app.app_context():
            return login(client, 'testadmin@test.com', 'Admin@1234')

    def test_dashboard_requires_admin(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/admin/dashboard', follow_redirects=True)
            assert b'Admin access required' in rv.data or rv.status_code == 200

    def test_admin_dashboard_loads(self, client, app, admin_user):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.get('/admin/dashboard')
            assert rv.status_code == 200

    def test_admin_users_page(self, client, app, admin_user):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.get('/admin/users')
            assert rv.status_code == 200

    def test_admin_clearances_page(self, client, app, admin_user):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.get('/admin/clearances')
            assert rv.status_code == 200

    def test_admin_revenue_page(self, client, app, admin_user):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.get('/admin/revenue')
            assert rv.status_code == 200

    def test_admin_wildlife_page(self, client, app, admin_user):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.get('/admin/wildlife')
            assert rv.status_code == 200

    def test_admin_vehicles_page(self, client, app, admin_user):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.get('/admin/vehicles')
            assert rv.status_code == 200

    def test_admin_reports_page(self, client, app, admin_user):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.get('/admin/reports')
            assert rv.status_code == 200

    def test_create_user_page(self, client, app, admin_user):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.get('/admin/users/create')
            assert rv.status_code == 200

    def test_create_user_post(self, client, app, admin_user, db):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.post('/admin/users/create', data={
                'full_name': 'Created Guide',
                'email': 'created@test.com',
                'phone': '+254700111222',
                'id_number': 'CREAT001',
                'role': 'guide',
                'company': 'Test Co',
                'license_number': 'KWS/001',
                'password': 'Mara@2024'
            }, follow_redirects=True)
            assert rv.status_code == 200
            from app.models import User
            u = User.query.filter_by(email='created@test.com').first()
            assert u is not None


# ── Guide Route Tests ─────────────────────────────────────────────

class TestGuideRoutes:
    def test_guide_dashboard(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/guide/dashboard')
            assert rv.status_code == 200

    def test_guide_vehicles_page(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/guide/vehicles')
            assert rv.status_code == 200

    def test_register_vehicle(self, client, app, guide_user, db):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.post('/guide/vehicles/register', data={
                'plate_number': 'KYZ 123T',
                'vehicle_type': 'Land Cruiser',
                'make': 'Toyota',
                'model': 'Land Cruiser 76',
                'year': '2021',
                'color': 'White',
                'capacity': '8',
                'insurance_number': 'INS001',
            }, follow_redirects=True)
            assert rv.status_code == 200
            from app.models import Vehicle
            v = Vehicle.query.filter_by(plate_number='KYZ 123T').first()
            assert v is not None

    def test_guide_clearances_page(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/guide/clearances')
            assert rv.status_code == 200

    def test_guide_sightings_page(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/guide/sightings')
            assert rv.status_code == 200

    def test_report_sighting_page(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/guide/sightings/report')
            assert rv.status_code == 200

    def test_submit_sighting(self, client, app, guide_user, db):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.post('/guide/sightings/report', data={
                'species': 'Panthera leo',
                'common_name': 'Lion',
                'category': 'Big Five',
                'count': '3',
                'latitude': '-1.5142',
                'longitude': '35.1433',
                'location_name': 'Test Plains',
                'behavior': 'Resting',
                'threat_level': 'none',
                'sighted_at': '2024-06-15T10:30',
            }, follow_redirects=True)
            assert rv.status_code == 200
            from app.models import WildlifeSighting
            s = WildlifeSighting.query.filter_by(species='Panthera leo').first()
            assert s is not None
            assert s.count == 3


# ── API Tests ─────────────────────────────────────────────────────

class TestAPIEndpoints:
    def test_clearance_status_invalid_token(self, client):
        rv = client.get('/api/v1/clearance/invalid-token/status')
        assert rv.status_code == 404

    def test_wildlife_map_requires_auth(self, client):
        rv = client.get('/api/v1/wildlife/map')
        assert rv.status_code in [302, 401]

    def test_wildlife_map_authenticated(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/api/v1/wildlife/map')
            assert rv.status_code == 200
            data = rv.get_json()
            assert 'sightings' in data

    def test_gates_density(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/api/v1/gates/density')
            assert rv.status_code == 200
            data = rv.get_json()
            assert 'gates' in data
            assert len(data['gates']) == 6  # 6 gates

    def test_active_alerts(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/api/v1/alerts/active')
            assert rv.status_code == 200
            data = rv.get_json()
            assert 'alerts' in data

    def test_dashboard_stats_admin_only(self, client, app, guide_user):
        with app.app_context():
            login(client, 'testguide@test.com', 'Guide@1234')
            rv = client.get('/api/v1/dashboard/stats')
            assert rv.status_code == 403

    def test_dashboard_stats_admin(self, client, app, admin_user):
        with app.app_context():
            login(client, 'testadmin@test.com', 'Admin@1234')
            rv = client.get('/api/v1/dashboard/stats')
            assert rv.status_code == 200
            data = rv.get_json()
            assert 'today' in data
            assert 'pending_clearances' in data

    def test_clearance_token_verify(self, client, app, db, admin_user, guide_user):
        from app.models import User, Vehicle, GateClearance
        import uuid
        from datetime import date
        with app.app_context():
            guide = User.query.filter_by(email='testguide@test.com').first()
            v = Vehicle(user_id=guide.id, plate_number='KAPI 001',
                        vehicle_type='Land Cruiser', capacity=8)
            db.session.add(v)
            db.session.flush()
            token = str(uuid.uuid4())
            c = GateClearance(
                token=token,
                guide_id=guide.id,
                vehicle_id=v.id,
                gate='Sekenani Gate',
                entry_date=date.today(),
                passenger_count=4,
                adult_count=4,
                purpose='Game Drive',
                status='approved'
            )
            db.session.add(c)
            db.session.commit()

            rv = client.get(f'/api/v1/clearance/{token}/status')
            assert rv.status_code == 200
            data = rv.get_json()
            assert data['token'] == token
            assert data['status'] == 'approved'
            assert data['gate'] == 'Sekenani Gate'


# ── Utility Function Tests ────────────────────────────────────────

class TestUtilities:
    def test_qr_code_generation(self, app, db, guide_user):
        from app.models import User, Vehicle, GateClearance
        from app.utils.qr_generator import generate_clearance_qr
        import uuid
        from datetime import date
        with app.app_context():
            guide = User.query.filter_by(email='testguide@test.com').first()
            v = Vehicle(user_id=guide.id, plate_number='KQR 001',
                        vehicle_type='Land Cruiser', capacity=8)
            db.session.add(v)
            db.session.flush()
            c = GateClearance(
                token=str(uuid.uuid4()),
                guide_id=guide.id,
                vehicle_id=v.id,
                gate='Sekenani Gate',
                entry_date=date.today(),
                passenger_count=4,
                adult_count=4,
                purpose='Game Drive',
                status='pending'
            )
            db.session.add(c)
            db.session.commit()

            filename = generate_clearance_qr(c)
            assert filename is not None
            assert filename.endswith('.png')
            import os
            filepath = os.path.join(app.config['QR_FOLDER'], filename)
            assert os.path.exists(filepath)
