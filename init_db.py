#!/usr/bin/env python3
"""
init_db.py — Initialize database, create all tables, and seed sample data.
Run once after setting up the project:
    python init_db.py
"""

import os
import sys
from datetime import datetime, date, timedelta, time
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('FLASK_ENV', 'development')

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import (User, Vehicle, GateClearance, Passenger,
                         WildlifeSighting, Revenue, Alert, AuditLog)


def create_admin(app):
    """Create default admin account."""
    with app.app_context():
        if User.query.filter_by(email='admin@maranaorok.go.ke').first():
            print('  ✓ Admin account already exists.')
            return

        admin = User(
            full_name='County Administrator',
            email='admin@maranaorok.go.ke',
            phone='+254700000001',
            id_number='ADMIN001',
            role='admin',
            is_active=True,
            is_verified=True,
            company='Narok County Government'
        )
        admin.set_password('Admin@2024')
        db.session.add(admin)
        db.session.commit()
        print(f'  ✓ Admin created: admin@maranaorok.go.ke / Admin@2024')
        return admin


def seed_guides(app):
    """Seed sample tour guides."""
    with app.app_context():
        guides_data = [
            {
                'full_name': 'John Kipchoge Moi',
                'email': 'guide@example.com',
                'phone': '+254712345678',
                'id_number': 'NID12345678',
                'license_number': 'KWS/TG/2021/001',
                'company': 'Mara Expeditions Ltd',
                'password': 'Guide@2024'
            },
            {
                'full_name': 'Mary Wanjiku Kamau',
                'email': 'mary@safarico.co.ke',
                'phone': '+254723456789',
                'id_number': 'NID23456789',
                'license_number': 'KWS/TG/2020/012',
                'company': 'Savanna Safari Co.',
                'password': 'Guide@2024'
            },
            {
                'full_name': 'Peter Omondi Onyango',
                'email': 'peter@wildlifekenya.ke',
                'phone': '+254734567890',
                'id_number': 'NID34567890',
                'license_number': 'KWS/TG/2022/034',
                'company': 'Kenya Wildlife Tours',
                'password': 'Guide@2024'
            },
        ]

        created = []
        for gd in guides_data:
            if User.query.filter_by(email=gd['email']).first():
                print(f"  ✓ Guide {gd['email']} already exists.")
                created.append(User.query.filter_by(email=gd['email']).first())
                continue
            guide = User(
                full_name=gd['full_name'],
                email=gd['email'],
                phone=gd['phone'],
                id_number=gd['id_number'],
                license_number=gd['license_number'],
                company=gd['company'],
                role='guide',
                is_active=True,
                is_verified=True
            )
            guide.set_password(gd['password'])
            db.session.add(guide)
            db.session.flush()
            created.append(guide)
            print(f"  ✓ Guide created: {gd['email']}")

        db.session.commit()
        return created


def seed_vehicles(app, guides):
    """Seed vehicles for guides."""
    with app.app_context():
        vehicles_data = [
            {'user_email': 'guide@example.com', 'plate': 'KCB 123A', 'type': 'Land Cruiser',
             'make': 'Toyota', 'model': 'Land Cruiser 76', 'year': 2019, 'color': 'White', 'capacity': 8,
             'insurance': 'INS/2024/001', 'expiry': date(2025, 6, 30)},
            {'user_email': 'guide@example.com', 'plate': 'KDD 456B', 'type': 'Land Rover',
             'make': 'Land Rover', 'model': 'Defender 110', 'year': 2021, 'color': 'Khaki', 'capacity': 9,
             'insurance': 'INS/2024/002', 'expiry': date(2025, 4, 15)},
            {'user_email': 'mary@safarico.co.ke', 'plate': 'KCC 789C', 'type': 'Minivan',
             'make': 'Toyota', 'model': 'Hiace', 'year': 2020, 'color': 'White', 'capacity': 14,
             'insurance': 'INS/2024/003', 'expiry': date(2025, 9, 20)},
            {'user_email': 'peter@wildlifekenya.ke', 'plate': 'KDA 321D', 'type': 'Land Cruiser',
             'make': 'Toyota', 'model': 'Land Cruiser Prado', 'year': 2022, 'color': 'Silver', 'capacity': 7,
             'insurance': 'INS/2024/004', 'expiry': date(2026, 1, 10)},
        ]

        created = []
        for vd in vehicles_data:
            if Vehicle.query.filter_by(plate_number=vd['plate']).first():
                print(f"  ✓ Vehicle {vd['plate']} already exists.")
                created.append(Vehicle.query.filter_by(plate_number=vd['plate']).first())
                continue
            user = User.query.filter_by(email=vd['user_email']).first()
            if not user:
                continue
            v = Vehicle(
                user_id=user.id,
                plate_number=vd['plate'],
                vehicle_type=vd['type'],
                make=vd['make'],
                model=vd['model'],
                year=vd['year'],
                color=vd['color'],
                capacity=vd['capacity'],
                insurance_number=vd['insurance'],
                insurance_expiry=vd['expiry'],
            )
            db.session.add(v)
            db.session.flush()
            created.append(v)
            print(f"  ✓ Vehicle created: {vd['plate']}")

        db.session.commit()
        return created


def seed_clearances(app):
    """Seed sample gate clearances and auto-generate revenue."""
    with app.app_context():
        admin = User.query.filter_by(role='admin').first()
        guide1 = User.query.filter_by(email='guide@example.com').first()
        guide2 = User.query.filter_by(email='mary@safarico.co.ke').first()
        guide3 = User.query.filter_by(email='peter@wildlifekenya.ke').first()
        v1 = Vehicle.query.filter_by(plate_number='KCB 123A').first()
        v2 = Vehicle.query.filter_by(plate_number='KDD 456B').first()
        v3 = Vehicle.query.filter_by(plate_number='KCC 789C').first()
        v4 = Vehicle.query.filter_by(plate_number='KDA 321D').first()

        if not all([guide1, v1]):
            print('  ✗ Cannot seed clearances: guides/vehicles missing.')
            return []

        today = date.today()
        clearances_data = [
            {'guide': guide1, 'vehicle': v1, 'gate': 'Sekenani Gate',
             'date': today - timedelta(days=5), 'time': time(7, 0),
             'adults': 5, 'children': 1, 'citizens': 2, 'non_citizens': 3,
             'purpose': 'Game Drive', 'status': 'approved'},
            {'guide': guide1, 'vehicle': v1, 'gate': 'Talek Gate',
             'date': today - timedelta(days=4), 'time': time(7, 30),
             'adults': 4, 'children': 0, 'citizens': 0, 'non_citizens': 4,
             'purpose': 'Photography', 'status': 'approved'},
            {'guide': guide2, 'vehicle': v3, 'gate': 'Musiara Gate',
             'date': today - timedelta(days=3), 'time': time(6, 30),
             'adults': 6, 'children': 2, 'citizens': 4, 'non_citizens': 2,
             'purpose': 'Game Drive', 'status': 'approved'},
            {'guide': guide1, 'vehicle': v2, 'gate': 'Oloololo Gate',
             'date': today - timedelta(days=2), 'time': time(8, 0),
             'adults': 5, 'children': 0, 'citizens': 1, 'non_citizens': 4,
             'purpose': 'Game Drive', 'status': 'approved'},
            {'guide': guide3, 'vehicle': v4, 'gate': 'Sand River Gate',
             'date': today - timedelta(days=1), 'time': time(7, 0),
             'adults': 6, 'children': 0, 'citizens': 2, 'non_citizens': 4,
             'purpose': 'Research', 'status': 'approved'},
            {'guide': guide2, 'vehicle': v3, 'gate': 'Sekenani Gate',
             'date': today, 'time': time(7, 0),
             'adults': 5, 'children': 2, 'citizens': 3, 'non_citizens': 2,
             'purpose': 'Game Drive', 'status': 'pending'},
            {'guide': guide3, 'vehicle': v4, 'gate': 'Talek Gate',
             'date': today + timedelta(days=1), 'time': time(7, 30),
             'adults': 4, 'children': 0, 'citizens': 0, 'non_citizens': 4,
             'purpose': 'Photography', 'status': 'pending'},
        ]

        created = []
        for cd in clearances_data:
            token = str(uuid.uuid4())
            c = GateClearance(
                token=token,
                guide_id=cd['guide'].id,
                vehicle_id=cd['vehicle'].id,
                gate=cd['gate'],
                entry_date=cd['date'],
                entry_time=cd['time'],
                adult_count=cd['adults'],
                child_count=cd['children'],
                citizen_count=cd['citizens'],
                non_citizen_count=cd['non_citizens'],
                passenger_count=cd['adults'] + cd['children'],
                purpose=cd['purpose'],
                status=cd['status'],
            )
            if cd['status'] == 'approved' and admin:
                c.approved_by = admin.id
                c.approved_at = datetime.utcnow() - timedelta(days=(date.today() - cd['date']).days)
                fee = c.calculate_fee()
                c.fee_paid = fee

            db.session.add(c)
            db.session.flush()

            # Revenue
            if cd['status'] == 'approved':
                r = Revenue(
                    clearance_id=c.id,
                    gate=cd['gate'],
                    amount=c.fee_paid or 0,
                    currency='KES',
                    payment_method='M-Pesa' if cd['guide'].id % 2 == 0 else 'Cash',
                    collected_by=admin.id if admin else None,
                )
                db.session.add(r)

            created.append(c)
            print(f"  ✓ Clearance created: {cd['gate']} ({cd['status']})")

        db.session.commit()
        return created


def seed_sightings(app):
    """Seed wildlife sightings data."""
    with app.app_context():
        guide1 = User.query.filter_by(email='guide@example.com').first()
        guide2 = User.query.filter_by(email='mary@safarico.co.ke').first()
        guide3 = User.query.filter_by(email='peter@wildlifekenya.ke').first()

        if not guide1:
            return

        sightings = [
            {'by': guide1, 'species': 'Panthera leo', 'common': 'Lion', 'cat': 'Big Five',
             'count': 4, 'lat': -1.5142, 'lng': 35.1433, 'loc': 'Near Sekenani River',
             'behavior': 'Resting', 'threat': 'none', 'days_ago': 5},
            {'by': guide1, 'species': 'Loxodonta africana', 'common': 'Elephant', 'cat': 'Big Five',
             'count': 12, 'lat': -1.5300, 'lng': 35.1600, 'loc': 'Mara Triangle',
             'behavior': 'Feeding', 'threat': 'none', 'days_ago': 5},
            {'by': guide2, 'species': 'Connochaetes taurinus', 'common': 'Wildebeest', 'cat': 'Plains Game',
             'count': 250, 'lat': -1.4500, 'lng': 35.0800, 'loc': 'Mara River Crossing',
             'behavior': 'Moving', 'threat': 'none', 'days_ago': 3},
            {'by': guide1, 'species': 'Panthera pardus', 'common': 'Leopard', 'cat': 'Big Five',
             'count': 1, 'lat': -1.5600, 'lng': 35.2100, 'loc': 'Talek River Banks',
             'behavior': 'Hunting', 'threat': 'medium', 'days_ago': 4},
            {'by': guide3, 'species': 'Acinonyx jubatus', 'common': 'Cheetah', 'cat': 'Predator',
             'count': 3, 'lat': -1.6400, 'lng': 35.3200, 'loc': 'Sand River Plains',
             'behavior': 'Hunting', 'threat': 'none', 'days_ago': 1},
            {'by': guide2, 'species': 'Diceros bicornis', 'common': 'Black Rhino', 'cat': 'Big Five',
             'count': 2, 'lat': -1.4200, 'lng': 35.0500, 'loc': 'Oloololo Escarpment',
             'behavior': 'Feeding', 'threat': 'high', 'days_ago': 3},
            {'by': guide1, 'species': 'Hippopotamus amphibius', 'common': 'Hippopotamus', 'cat': 'Other Mammal',
             'count': 8, 'lat': -1.5800, 'lng': 35.1000, 'loc': 'Mara River Pool',
             'behavior': 'Resting', 'threat': 'none', 'days_ago': 2},
            {'by': guide3, 'species': 'Equus quagga', 'common': 'Plains Zebra', 'cat': 'Plains Game',
             'count': 60, 'lat': -1.6500, 'lng': 35.3000, 'loc': 'Sand River Floodplains',
             'behavior': 'Feeding', 'threat': 'none', 'days_ago': 1},
            {'by': guide1, 'species': 'Syncerus caffer', 'common': 'African Buffalo', 'cat': 'Big Five',
             'count': 35, 'lat': -1.5450, 'lng': 35.1850, 'loc': 'South Mara Triangle',
             'behavior': 'Moving', 'threat': 'none', 'days_ago': 0},
            {'by': guide2, 'species': 'Crocodylus niloticus', 'common': 'Nile Crocodile', 'cat': 'Reptile',
             'count': 5, 'lat': -1.5000, 'lng': 35.1500, 'loc': 'Mara River Crossing',
             'behavior': 'Resting', 'threat': 'low', 'days_ago': 0},
            {'by': guide1, 'species': 'Crocuta crocuta', 'common': 'Spotted Hyena', 'cat': 'Predator',
             'count': 6, 'lat': -1.5200, 'lng': 35.1800, 'loc': 'Sekenani Valley',
             'behavior': 'Moving', 'threat': 'none', 'days_ago': 2},
            {'by': guide3, 'species': 'Giraffa camelopardalis', 'common': 'Giraffe', 'cat': 'Plains Game',
             'count': 7, 'lat': -1.6100, 'lng': 35.2800, 'loc': 'Acacia Woodland',
             'behavior': 'Feeding', 'threat': 'none', 'days_ago': 1},
        ]

        for sd in sightings:
            s = WildlifeSighting(
                reported_by=sd['by'].id,
                species=sd['species'],
                common_name=sd['common'],
                category=sd['cat'],
                count=sd['count'],
                latitude=sd['lat'],
                longitude=sd['lng'],
                location_name=sd['loc'],
                behavior=sd['behavior'],
                threat_level=sd['threat'],
                sighted_at=datetime.utcnow() - timedelta(days=sd['days_ago'], hours=2),
                is_verified=sd['days_ago'] > 1
            )
            db.session.add(s)
            print(f"  ✓ Sighting: {sd['common']} (x{sd['count']}) at {sd['loc']}")

        db.session.commit()


def seed_alerts(app):
    """Seed system alerts."""
    with app.app_context():
        admin = User.query.filter_by(role='admin').first()
        if Alert.query.count() > 0:
            print('  ✓ Alerts already seeded.')
            return

        alerts = [
            ('Wildebeest Migration Active', 'Great Wildebeest Migration is active near Mara River crossings. Expect high vehicle density at Talek and Sand River gates.', 'info'),
            ('Black Rhino Sighting — Restricted Area', 'Black rhino mother and calf spotted near Oloololo Escarpment. Maintain 200m minimum distance. No off-road driving.', 'warning'),
            ('Road Notice — Musiara Gate', 'Access road under maintenance. Use alternative Oloololo route. Expected completion in 3 days.', 'danger'),
        ]

        for title, msg, atype in alerts:
            a = Alert(title=title, message=msg, alert_type=atype,
                      created_by=admin.id if admin else None, is_active=True)
            db.session.add(a)
            print(f'  ✓ Alert: {title}')

        db.session.commit()


def main():
    print('\n══════════════════════════════════════════════════')
    print('  MaraGate System — Database Initialization')
    print('══════════════════════════════════════════════════\n')

    app = create_app('development')

    with app.app_context():
        print('▶ Creating database tables…')
        db.create_all()
        print('  ✓ Tables created.\n')

        print('▶ Creating admin account…')
        create_admin(app)
        print()

        print('▶ Seeding tour guides…')
        guides = seed_guides(app)
        print()

        print('▶ Seeding vehicles…')
        vehicles = seed_vehicles(app, guides)
        print()

        print('▶ Seeding gate clearances & revenue…')
        seed_clearances(app)
        print()

        print('▶ Seeding wildlife sightings…')
        seed_sightings(app)
        print()

        print('▶ Seeding alerts…')
        seed_alerts(app)
        print()

    print('══════════════════════════════════════════════════')
    print('  ✓ Initialization complete!')
    print()
    print('  Login credentials:')
    print('  Admin : admin@maranaorok.go.ke  /  Admin@2024')
    print('  Guide : guide@example.com       /  Guide@2024')
    print('══════════════════════════════════════════════════\n')


if __name__ == '__main__':
    main()
