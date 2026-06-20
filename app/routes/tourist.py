from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models import User, Vehicle, GateClearance, Passenger, Revenue
from app.utils.qr_generator import generate_clearance_qr
from datetime import datetime, date
import uuid

tourist_bp = Blueprint('tourist', __name__)

GATES = [
    'Sekenani Gate', 'Oloololo Gate', 'Talek Gate',
    'Musiara Gate', 'Sand River Gate', 'Ololaimutia Gate'
]

PURPOSES = [
    'Game Drive', 'Research', 'Photography',
    'Balloon Safari', 'Walking Safari', 'Night Drive', 'Other'
]


@tourist_bp.route('/book')
@login_required
def book():
    """Step 1 — Choose a guide and vehicle."""
    guides = User.query.filter_by(role='guide', is_active=True, is_verified=True).all()
    # Get vehicles for each guide
    guide_data = []
    for g in guides:
        vehicles = Vehicle.query.filter_by(user_id=g.id, is_active=True).all()
        if vehicles:
            guide_data.append({
                'guide': g,
                'vehicles': vehicles
            })
    return render_template('tourist/book_step1.html', guide_data=guide_data)


@tourist_bp.route('/book/details', methods=['GET', 'POST'])
@login_required
def book_details():
    """Step 2 — Enter trip details."""
    guide_id   = request.args.get('guide_id',   type=int) or request.form.get('guide_id',   type=int)
    vehicle_id = request.args.get('vehicle_id', type=int) or request.form.get('vehicle_id', type=int)

    guide   = User.query.get_or_404(guide_id)
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=guide_id).first_or_404()

    if request.method == 'POST':
        # Save booking details in session
        session['booking'] = {
            'guide_id':         guide_id,
            'vehicle_id':       vehicle_id,
            'gate':             request.form.get('gate'),
            'entry_date':       request.form.get('entry_date'),
            'entry_time':       request.form.get('entry_time', '07:00'),
            'purpose':          request.form.get('purpose', 'Game Drive'),
            'adult_count':      int(request.form.get('adult_count', 1)),
            'child_count':      int(request.form.get('child_count', 0)),
            'citizen_count':    int(request.form.get('citizen_count', 0)),
            'non_citizen_count':int(request.form.get('non_citizen_count', 1)),
        }
        return redirect(url_for('tourist.book_passengers'))

    return render_template('tourist/book_step2.html',
                           guide=guide, vehicle=vehicle,
                           gates=GATES, purposes=PURPOSES,
                           today=date.today().isoformat())


@tourist_bp.route('/book/passengers', methods=['GET', 'POST'])
@login_required
def book_passengers():
    """Step 3 — Add passengers."""
    booking = session.get('booking')
    if not booking:
        return redirect(url_for('tourist.book'))

    if request.method == 'POST':
        session['passengers'] = {
            'names':        request.form.getlist('name[]'),
            'nationalities':request.form.getlist('nationality[]'),
            'passports':    request.form.getlist('passport[]'),
            'age_groups':   request.form.getlist('age_group[]'),
        }
        return redirect(url_for('tourist.book_payment'))

    adult_count = booking.get('adult_count', 1)
    child_count = booking.get('child_count', 0)
    total_pax   = adult_count + child_count

    return render_template('tourist/book_step3.html',
                           booking=booking, total_pax=total_pax)


@tourist_bp.route('/book/payment', methods=['GET', 'POST'])
@login_required
def book_payment():
    """Step 4 — Payment page."""
    booking    = session.get('booking')
    passengers = session.get('passengers')
    if not booking:
        return redirect(url_for('tourist.book'))

    # Calculate fee
    citizen     = booking.get('citizen_count', 0)
    non_citizen = booking.get('non_citizen_count', 1)
    children    = booking.get('child_count', 0)
    fee = (citizen * 215) + (non_citizen * 80 * 130) + (children * 105) + 350

    vehicle = Vehicle.query.get(booking['vehicle_id'])
    guide   = User.query.get(booking['guide_id'])

    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'M-Pesa')
        mpesa_ref      = request.form.get('mpesa_ref', '').strip()

        # Create the clearance
        try:
            entry_date = datetime.strptime(booking['entry_date'], '%Y-%m-%d').date()
            entry_time = datetime.strptime(booking.get('entry_time', '07:00'), '%H:%M').time()
        except Exception:
            entry_date = date.today()
            entry_time = None

        clearance = GateClearance(
            token            = str(uuid.uuid4()),
            guide_id         = booking['guide_id'],
            vehicle_id       = booking['vehicle_id'],
            gate             = booking['gate'],
            entry_date       = entry_date,
            entry_time       = entry_time,
            adult_count      = booking.get('adult_count', 1),
            child_count      = booking.get('child_count', 0),
            citizen_count    = booking.get('citizen_count', 0),
            non_citizen_count= booking.get('non_citizen_count', 1),
            passenger_count  = booking.get('adult_count', 1) + booking.get('child_count', 0),
            purpose          = booking.get('purpose', 'Game Drive'),
            status           = 'pending',
            fee_paid         = fee,
            fee_currency     = 'KES',
            notes            = f'Booked by tourist: {current_user.full_name}. Payment: {payment_method}.'
        )
        db.session.add(clearance)
        db.session.flush()

        # Add passengers
        if passengers:
            names        = passengers.get('names', [])
            nationalities= passengers.get('nationalities', [])
            passports    = passengers.get('passports', [])
            age_groups   = passengers.get('age_groups', [])
            for i, name in enumerate(names):
                if name.strip():
                    p = Passenger(
                        clearance_id = clearance.id,
                        full_name    = name.strip(),
                        nationality  = nationalities[i] if i < len(nationalities) else '',
                        passport_id  = passports[i]    if i < len(passports)     else '',
                        age_group    = age_groups[i]   if i < len(age_groups)    else 'adult',
                        is_citizen   = (nationalities[i].lower() == 'kenyan') if i < len(nationalities) else False
                    )
                    db.session.add(p)

        # Revenue record
        revenue = Revenue(
            clearance_id   = clearance.id,
            gate           = booking['gate'],
            amount         = fee,
            currency       = 'KES',
            payment_method = payment_method,
            mpesa_ref      = mpesa_ref or None,
        )
        db.session.add(revenue)

        # Generate QR
        db.session.commit()
        try:
            qr_path = generate_clearance_qr(clearance)
            clearance.qr_code_path = qr_path
            db.session.commit()
        except Exception:
            pass

        # Clear session booking
        session.pop('booking',    None)
        session.pop('passengers', None)

        flash('Booking submitted successfully! Awaiting admin approval.', 'success')
        return redirect(url_for('tourist.book_confirm', clearance_id=clearance.id))

    return render_template('tourist/book_step4.html',
                           booking=booking, fee=fee,
                           vehicle=vehicle, guide=guide)


@tourist_bp.route('/book/confirm/<int:clearance_id>')
@login_required
def book_confirm(clearance_id):
    """Step 5 — Confirmation page with QR code."""
    clearance  = GateClearance.query.get_or_404(clearance_id)
    passengers = Passenger.query.filter_by(clearance_id=clearance_id).all()
    return render_template('tourist/book_confirm.html',
                           clearance=clearance, passengers=passengers)


@tourist_bp.route('/my-bookings')
@login_required
def my_bookings():
    """View all bookings made by the logged-in user."""
    # Show clearances where user is the guide OR where user's name is in notes
    clearances = GateClearance.query.filter(
        GateClearance.notes.like(f'%{current_user.full_name}%')
    ).order_by(GateClearance.created_at.desc()).all()

    # Also show if user IS the guide
    guide_clearances = GateClearance.query.filter_by(
        guide_id=current_user.id
    ).order_by(GateClearance.created_at.desc()).all()

    # Merge and deduplicate
    all_ids   = set()
    all_clears = []
    for c in list(clearances) + list(guide_clearances):
        if c.id not in all_ids:
            all_ids.add(c.id)
            all_clears.append(c)

    all_clears.sort(key=lambda x: x.created_at, reverse=True)
    return render_template('tourist/my_bookings.html', clearances=all_clears)


@tourist_bp.route('/api/vehicles/<int:guide_id>')
@login_required
def get_guide_vehicles(guide_id):
    """API: get vehicles for a guide (for dynamic dropdowns)."""
    vehicles = Vehicle.query.filter_by(user_id=guide_id, is_active=True).all()
    return jsonify([{
        'id':       v.id,
        'plate':    v.plate_number,
        'type':     v.vehicle_type,
        'capacity': v.capacity,
        'color':    v.color or ''
    } for v in vehicles])
