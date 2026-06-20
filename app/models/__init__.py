from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=generate_uuid)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    id_number = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('admin', 'guide'), nullable=False, default='guide')
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    profile_photo = db.Column(db.String(256))
    license_number = db.Column(db.String(50))  # Guide license
    company = db.Column(db.String(120))  # Tour company
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    vehicles = db.relationship('Vehicle', backref='owner', lazy='dynamic', foreign_keys='Vehicle.user_id')
    clearances = db.relationship('GateClearance', backref='guide', lazy='dynamic', foreign_keys='GateClearance.guide_id')
    sightings = db.relationship('WildlifeSighting', backref='reporter', lazy='dynamic', foreign_keys='WildlifeSighting.reported_by')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_type = db.Column(db.Enum(
        'Land Cruiser', 'Land Rover', 'Minivan', 'Bus', 'Motorcycle', 'Other'
    ), nullable=False)
    make = db.Column(db.String(60))
    model = db.Column(db.String(60))
    year = db.Column(db.Integer)
    color = db.Column(db.String(30))
    capacity = db.Column(db.Integer, default=7)
    insurance_number = db.Column(db.String(60))
    insurance_expiry = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    clearances = db.relationship('GateClearance', backref='vehicle', lazy='dynamic')

    def __repr__(self):
        return f'<Vehicle {self.plate_number}>'


class GateClearance(db.Model):
    __tablename__ = 'gate_clearances'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, default=generate_uuid)
    guide_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    gate = db.Column(db.Enum(
        'Sekenani Gate', 'Oloololo Gate', 'Talek Gate', 'Musiara Gate',
        'Sand River Gate', 'Ololaimutia Gate'
    ), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    entry_time = db.Column(db.Time)
    exit_date = db.Column(db.Date)
    exit_time = db.Column(db.Time)
    passenger_count = db.Column(db.Integer, default=0)
    adult_count = db.Column(db.Integer, default=0)
    child_count = db.Column(db.Integer, default=0)
    citizen_count = db.Column(db.Integer, default=0)
    non_citizen_count = db.Column(db.Integer, default=0)
    purpose = db.Column(db.Enum(
        'Game Drive', 'Research', 'Photography', 'Balloon Safari',
        'Walking Safari', 'Night Drive', 'Other'
    ), default='Game Drive')
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'expired'), default='pending')
    qr_code_path = db.Column(db.String(256))
    manifest_path = db.Column(db.String(256))
    fee_paid = db.Column(db.Numeric(10, 2), default=0.00)
    fee_currency = db.Column(db.String(3), default='KES')
    notes = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    approver = db.relationship('User', foreign_keys=[approved_by])
    passengers = db.relationship('Passenger', backref='clearance', lazy='dynamic', cascade='all, delete-orphan')

    def calculate_fee(self):
        """Calculate gate fee based on passenger counts"""
        adult_citizen = 215  # KES
        adult_non_citizen = 80  # USD equivalent
        child_citizen = 105
        child_non_citizen = 45
        vehicle_fee = 350

        fee = (self.citizen_count * adult_citizen +
               self.non_citizen_count * adult_non_citizen * 130 +
               self.child_count * child_citizen +
               vehicle_fee)
        return fee

    def __repr__(self):
        return f'<GateClearance {self.token}>'


class Passenger(db.Model):
    __tablename__ = 'passengers'

    id = db.Column(db.Integer, primary_key=True)
    clearance_id = db.Column(db.Integer, db.ForeignKey('gate_clearances.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    nationality = db.Column(db.String(60))
    passport_id = db.Column(db.String(40))
    age_group = db.Column(db.Enum('adult', 'child'), default='adult')
    is_citizen = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Passenger {self.full_name}>'


class WildlifeSighting(db.Model):
    __tablename__ = 'wildlife_sightings'

    id = db.Column(db.Integer, primary_key=True)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    clearance_id = db.Column(db.Integer, db.ForeignKey('gate_clearances.id'), nullable=True)
    species = db.Column(db.String(100), nullable=False)
    common_name = db.Column(db.String(100))
    category = db.Column(db.Enum(
        'Big Five', 'Plains Game', 'Predator', 'Primate', 'Bird',
        'Reptile', 'Other Mammal'
    ), default='Plains Game')
    count = db.Column(db.Integer, default=1)
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    location_name = db.Column(db.String(120))
    behavior = db.Column(db.Enum(
        'Feeding', 'Resting', 'Moving', 'Hunting', 'Playing',
        'Mating', 'Drinking', 'Other'
    ), default='Other')
    notes = db.Column(db.Text)
    sighted_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    threat_level = db.Column(db.Enum('none', 'low', 'medium', 'high'), default='none')

    photos = db.relationship('SightingPhoto', backref='sighting', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<WildlifeSighting {self.species}>'


class SightingPhoto(db.Model):
    __tablename__ = 'sighting_photos'

    id = db.Column(db.Integer, primary_key=True)
    sighting_id = db.Column(db.Integer, db.ForeignKey('wildlife_sightings.id'), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256))
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Revenue(db.Model):
    __tablename__ = 'revenue_records'

    id = db.Column(db.Integer, primary_key=True)
    clearance_id = db.Column(db.Integer, db.ForeignKey('gate_clearances.id'), nullable=False)
    gate = db.Column(db.String(60))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='KES')
    payment_method = db.Column(db.Enum('Cash', 'M-Pesa', 'Card', 'Bank Transfer'), default='Cash')
    mpesa_ref = db.Column(db.String(30))
    collected_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    collected_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    clearance = db.relationship('GateClearance', backref='revenue_record')
    collector = db.relationship('User', foreign_keys=[collected_by])


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.Enum('info', 'warning', 'danger', 'success'), default='info')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    creator = db.relationship('User', foreign_keys=[created_by])


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
