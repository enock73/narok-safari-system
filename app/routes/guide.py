from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app, send_file)
from flask_login import login_required, current_user
from app import db
from app.models import (Vehicle, GateClearance, WildlifeSighting,
                         SightingPhoto, Passenger, Alert)
from app.utils.qr_generator import generate_clearance_qr
from datetime import datetime, date
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy import func

guide_bp = Blueprint('guide', __name__)

GATES = [
    'Sekenani Gate', 'Oloololo Gate', 'Talek Gate',
    'Musiara Gate', 'Sand River Gate', 'Ololaimutia Gate'
]

PURPOSES = ['Game Drive', 'Research', 'Photography', 'Balloon Safari',
            'Walking Safari', 'Night Drive', 'Other']


def allowed_file(filename, allowed_extensions):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in allowed_extensions)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@guide_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()

    my_vehicles = Vehicle.query.filter_by(user_id=current_user.id, is_active=True).all()
    pending = GateClearance.query.filter_by(
        guide_id=current_user.id, status='pending'
    ).count()
    approved_today = GateClearance.query.filter_by(
        guide_id=current_user.id, status='approved'
    ).filter(func.date(GateClearance.entry_date) == today).count()
    total_clearances = GateClearance.query.filter_by(guide_id=current_user.id).count()
    my_sightings = WildlifeSighting.query.filter_by(reported_by=current_user.id).count()

    recent = GateClearance.query.filter_by(
        guide_id=current_user.id
    ).order_by(GateClearance.created_at.desc()).limit(5).all()

    alerts = Alert.query.filter_by(is_active=True).order_by(
        Alert.created_at.desc()
    ).limit(3).all()

    return render_template('guide/dashboard.html',
        my_vehicles=my_vehicles,
        pending=pending,
        approved_today=approved_today,
        total_clearances=total_clearances,
        my_sightings=my_sightings,
        recent=recent,
        alerts=alerts
    )


# ── Vehicles ──────────────────────────────────────────────────────────────────

@guide_bp.route('/vehicles')
@login_required
def vehicles():
    my_vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    return render_template('guide/vehicles.html', vehicles=my_vehicles)


@guide_bp.route('/vehicles/register', methods=['GET', 'POST'])
@login_required
def register_vehicle():
    if request.method == 'POST':
        plate = request.form.get('plate_number', '').strip().upper()
        if Vehicle.query.filter_by(plate_number=plate).first():
            flash('Vehicle with this plate number already registered.', 'danger')
            return render_template('guide/register_vehicle.html')

        vehicle = Vehicle(
            user_id=current_user.id,
            plate_number=plate,
            vehicle_type=request.form.get('vehicle_type'),
            make=request.form.get('make'),
            model=request.form.get('model'),
            year=request.form.get('year', type=int),
            color=request.form.get('color'),
            capacity=request.form.get('capacity', 7, type=int),
            insurance_number=request.form.get('insurance_number'),
        )
        expiry = request.form.get('insurance_expiry')
        if expiry:
            vehicle.insurance_expiry = datetime.strptime(expiry, '%Y-%m-%d').date()

        db.session.add(vehicle)
        db.session.commit()
        flash(f'Vehicle {plate} registered successfully.', 'success')
        return redirect(url_for('guide.vehicles'))

    return render_template('guide/register_vehicle.html')


@guide_bp.route('/vehicles/<int:vehicle_id>/delete', methods=['POST'])
@login_required
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    vehicle.is_active = False
    db.session.commit()
    flash('Vehicle removed.', 'info')
    return redirect(url_for('guide.vehicles'))


# ── Gate Clearance ────────────────────────────────────────────────────────────

@guide_bp.route('/clearances')
@login_required
def clearances():
    page = request.args.get('page', 1, type=int)
    clearances_list = GateClearance.query.filter_by(
        guide_id=current_user.id
    ).order_by(GateClearance.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('guide/clearances.html', clearances=clearances_list)


@guide_bp.route('/clearances/request', methods=['GET', 'POST'])
@login_required
def request_clearance():
    vehicles = Vehicle.query.filter_by(user_id=current_user.id, is_active=True).all()

    if not vehicles:
        flash('Please register a vehicle before requesting clearance.', 'warning')
        return redirect(url_for('guide.register_vehicle'))

    if request.method == 'POST':
        vehicle_id = request.form.get('vehicle_id', type=int)
        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first()
        if not vehicle:
            flash('Invalid vehicle selection.', 'danger')
            return render_template('guide/request_clearance.html', vehicles=vehicles, gates=GATES, purposes=PURPOSES)

        entry_date_str = request.form.get('entry_date')
        try:
            entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid entry date.', 'danger')
            return render_template('guide/request_clearance.html', vehicles=vehicles, gates=GATES, purposes=PURPOSES)

        entry_time_str = request.form.get('entry_time', '07:00')
        try:
            entry_time = datetime.strptime(entry_time_str, '%H:%M').time()
        except ValueError:
            entry_time = None

        adult_count = request.form.get('adult_count', 0, type=int)
        child_count = request.form.get('child_count', 0, type=int)
        citizen_count = request.form.get('citizen_count', 0, type=int)
        non_citizen_count = request.form.get('non_citizen_count', 0, type=int)

        clearance = GateClearance(
            guide_id=current_user.id,
            vehicle_id=vehicle_id,
            gate=request.form.get('gate'),
            entry_date=entry_date,
            entry_time=entry_time,
            adult_count=adult_count,
            child_count=child_count,
            citizen_count=citizen_count,
            non_citizen_count=non_citizen_count,
            passenger_count=adult_count + child_count,
            purpose=request.form.get('purpose', 'Game Drive'),
            status='pending'
        )
        db.session.add(clearance)
        db.session.flush()  # get ID

        # Handle manifest upload
        if 'manifest' in request.files:
            f = request.files['manifest']
            if f and f.filename and allowed_file(f.filename, {'pdf', 'xlsx', 'csv'}):
                filename = secure_filename(f'manifest_{clearance.id}_{uuid.uuid4().hex[:8]}.{f.filename.rsplit(".", 1)[1].lower()}')
                f.save(os.path.join(current_app.config['MANIFEST_FOLDER'], filename))
                clearance.manifest_path = filename

        # Add passengers
        names = request.form.getlist('passenger_name[]')
        nationalities = request.form.getlist('passenger_nationality[]')
        passports = request.form.getlist('passenger_passport[]')
        age_groups = request.form.getlist('passenger_age_group[]')
        for i, name in enumerate(names):
            if name.strip():
                p = Passenger(
                    clearance_id=clearance.id,
                    full_name=name.strip(),
                    nationality=nationalities[i] if i < len(nationalities) else '',
                    passport_id=passports[i] if i < len(passports) else '',
                    age_group=age_groups[i] if i < len(age_groups) else 'adult',
                    is_citizen=(nationalities[i].lower() == 'kenyan') if i < len(nationalities) else False
                )
                db.session.add(p)

        # Generate QR code
        db.session.commit()
        qr_path = generate_clearance_qr(clearance)
        clearance.qr_code_path = qr_path
        db.session.commit()

        flash('Gate clearance request submitted! Awaiting admin approval.', 'success')
        return redirect(url_for('guide.clearance_detail', clearance_id=clearance.id))

    return render_template('guide/request_clearance.html',
                           vehicles=vehicles, gates=GATES, purposes=PURPOSES)


@guide_bp.route('/clearances/<int:clearance_id>')
@login_required
def clearance_detail(clearance_id):
    clearance = GateClearance.query.filter_by(
        id=clearance_id, guide_id=current_user.id
    ).first_or_404()
    passengers = Passenger.query.filter_by(clearance_id=clearance_id).all()
    return render_template('guide/clearance_detail.html',
                           clearance=clearance, passengers=passengers)


@guide_bp.route('/clearances/<int:clearance_id>/qr')
@login_required
def view_qr(clearance_id):
    clearance = GateClearance.query.filter_by(
        id=clearance_id, guide_id=current_user.id
    ).first_or_404()
    return render_template('guide/view_qr.html', clearance=clearance)


# ── Wildlife Sightings ────────────────────────────────────────────────────────

@guide_bp.route('/sightings')
@login_required
def sightings():
    page = request.args.get('page', 1, type=int)
    sightings_list = WildlifeSighting.query.filter_by(
        reported_by=current_user.id
    ).order_by(WildlifeSighting.sighted_at.desc()).paginate(page=page, per_page=15)
    return render_template('guide/sightings.html', sightings=sightings_list)


@guide_bp.route('/sightings/report', methods=['GET', 'POST'])
@login_required
def report_sighting():
    if request.method == 'POST':
        try:
            lat = float(request.form.get('latitude'))
            lng = float(request.form.get('longitude'))
        except (TypeError, ValueError):
            flash('Valid GPS coordinates are required.', 'danger')
            return render_template('guide/report_sighting.html')

        sighted_str = request.form.get('sighted_at') or datetime.utcnow().strftime('%Y-%m-%dT%H:%M')
        try:
            sighted_at = datetime.strptime(sighted_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            sighted_at = datetime.utcnow()

        sighting = WildlifeSighting(
            reported_by=current_user.id,
            species=request.form.get('species'),
            common_name=request.form.get('common_name'),
            category=request.form.get('category', 'Plains Game'),
            count=request.form.get('count', 1, type=int),
            latitude=lat,
            longitude=lng,
            location_name=request.form.get('location_name'),
            behavior=request.form.get('behavior', 'Other'),
            notes=request.form.get('notes'),
            threat_level=request.form.get('threat_level', 'none'),
            sighted_at=sighted_at
        )

        clearance_id = request.form.get('clearance_id', type=int)
        if clearance_id:
            sighting.clearance_id = clearance_id

        db.session.add(sighting)
        db.session.flush()

        # Handle photo uploads
        photos = request.files.getlist('photos[]')
        for photo in photos:
            if photo and photo.filename and allowed_file(
                photo.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']
            ):
                ext = photo.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f'sighting_{sighting.id}_{uuid.uuid4().hex[:8]}.{ext}')
                photo.save(os.path.join(current_app.config['PHOTO_FOLDER'], filename))
                sp = SightingPhoto(
                    sighting_id=sighting.id,
                    filename=filename,
                    original_name=photo.filename,
                )
                db.session.add(sp)

        db.session.commit()
        flash('Wildlife sighting reported successfully!', 'success')
        return redirect(url_for('guide.sightings'))

    # Pass active clearances for linking
    my_clearances = GateClearance.query.filter_by(
        guide_id=current_user.id, status='approved'
    ).order_by(GateClearance.entry_date.desc()).limit(10).all()

    categories = ['Big Five', 'Plains Game', 'Predator', 'Primate', 'Bird', 'Reptile', 'Other Mammal']
    behaviors = ['Feeding', 'Resting', 'Moving', 'Hunting', 'Playing', 'Mating', 'Drinking', 'Other']

    return render_template('guide/report_sighting.html',
        my_clearances=my_clearances,
        categories=categories,
        behaviors=behaviors
    )
