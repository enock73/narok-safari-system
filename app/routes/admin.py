from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models import (User, Vehicle, GateClearance, WildlifeSighting,
                         Revenue, Alert, AuditLog, Passenger)
from app.utils.reports import generate_pdf_report, generate_excel_report
from functools import wraps
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
import json

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    today = date.today()
    month_start = today.replace(day=1)

    # Stats
    total_guides = User.query.filter_by(role='guide').count()
    total_vehicles = Vehicle.query.count()
    pending_clearances = GateClearance.query.filter_by(status='pending').count()
    today_clearances = GateClearance.query.filter(
        func.date(GateClearance.entry_date) == today
    ).count()

    # Revenue stats
    month_revenue = db.session.query(func.sum(Revenue.amount)).filter(
        Revenue.collected_at >= month_start
    ).scalar() or 0

    today_revenue = db.session.query(func.sum(Revenue.amount)).filter(
        func.date(Revenue.collected_at) == today
    ).scalar() or 0

    # Recent clearances
    recent_clearances = GateClearance.query.order_by(
        GateClearance.created_at.desc()
    ).limit(10).all()

    # Wildlife sightings today
    today_sightings = WildlifeSighting.query.filter(
        func.date(WildlifeSighting.sighted_at) == today
    ).count()

    # Revenue by gate (last 30 days) — convert Decimal to float
    gate_revenue_raw = db.session.query(
        Revenue.gate,
        func.sum(Revenue.amount).label('total')
    ).filter(
        Revenue.collected_at >= today - timedelta(days=30)
    ).group_by(Revenue.gate).all()

    gate_revenue = [(g, float(t)) for g, t in gate_revenue_raw]

    # Serialize for JS doughnut chart
    gate_revenue_json = json.dumps([
        {'gate': g, 'total': float(t)} for g, t in gate_revenue_raw
    ])

    # Daily clearances last 7 days
    daily_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = GateClearance.query.filter(
            func.date(GateClearance.entry_date) == d
        ).count()
        daily_data.append({'date': d.strftime('%a %d'), 'count': count})

    # Active alerts
    alerts = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).limit(5).all()

    # Top species — convert to plain types
    top_species_raw = db.session.query(
        WildlifeSighting.species,
        func.sum(WildlifeSighting.count).label('total')
    ).group_by(WildlifeSighting.species).order_by(func.sum(WildlifeSighting.count).desc()).limit(5).all()

    top_species = [(s, int(t)) for s, t in top_species_raw]

    return render_template('admin/dashboard.html',
        total_guides=total_guides,
        total_vehicles=total_vehicles,
        pending_clearances=pending_clearances,
        today_clearances=today_clearances,
        month_revenue=float(month_revenue),
        today_revenue=float(today_revenue),
        recent_clearances=recent_clearances,
        today_sightings=today_sightings,
        gate_revenue=gate_revenue,
        gate_revenue_json=gate_revenue_json,
        daily_data=json.dumps(daily_data),
        alerts=alerts,
        top_species=top_species
    )


# ── User Management ──────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if search:
        query = query.filter(
            (User.full_name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )

    users_list = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users_list, search=search, role_filter=role_filter)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate yourself'}), 400
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'suspended'
    flash(f'User {user.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    flash(f'{user.full_name} has been verified.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('admin/create_user.html')

        user = User(
            full_name=request.form.get('full_name'),
            email=email,
            phone=request.form.get('phone'),
            id_number=request.form.get('id_number'),
            role=request.form.get('role', 'guide'),
            company=request.form.get('company'),
            license_number=request.form.get('license_number'),
            is_verified=True
        )
        user.set_password(request.form.get('password', 'Mara@2024'))
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.full_name} created successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/create_user.html')


# ── Gate Clearances ───────────────────────────────────────────────────────────

@admin_bp.route('/clearances')
@login_required
@admin_required
def clearances():
    status_filter = request.args.get('status', '')
    gate_filter = request.args.get('gate', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)

    query = GateClearance.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if gate_filter:
        query = query.filter_by(gate=gate_filter)
    if date_from:
        query = query.filter(GateClearance.entry_date >= date_from)
    if date_to:
        query = query.filter(GateClearance.entry_date <= date_to)

    clearances_list = query.order_by(GateClearance.created_at.desc()).paginate(page=page, per_page=20)

    gates = [
        'Sekenani Gate', 'Oloololo Gate', 'Talek Gate',
        'Musiara Gate', 'Sand River Gate', 'Ololaimutia Gate'
    ]
    return render_template('admin/clearances.html',
        clearances=clearances_list, gates=gates,
        status_filter=status_filter, gate_filter=gate_filter,
        date_from=date_from, date_to=date_to
    )


@admin_bp.route('/clearances/<int:clearance_id>')
@login_required
@admin_required
def clearance_detail(clearance_id):
    clearance = GateClearance.query.get_or_404(clearance_id)
    passengers = Passenger.query.filter_by(clearance_id=clearance_id).all()
    return render_template('admin/clearance_detail.html',
                           clearance=clearance, passengers=passengers)


@admin_bp.route('/clearances/<int:clearance_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_clearance(clearance_id):
    clearance = GateClearance.query.get_or_404(clearance_id)
    notes = request.form.get('notes', '')

    clearance.status = 'approved'
    clearance.approved_by = current_user.id
    clearance.approved_at = datetime.utcnow()
    if notes:
        clearance.notes = notes

    # Auto-create revenue record
    fee = clearance.calculate_fee()
    revenue = Revenue(
        clearance_id=clearance.id,
        gate=clearance.gate,
        amount=fee,
        currency='KES',
        collected_by=current_user.id
    )
    db.session.add(revenue)
    clearance.fee_paid = fee
    db.session.commit()

    flash(f'Clearance approved. Fee: KES {fee:,.0f}', 'success')
    return redirect(url_for('admin.clearances'))


@admin_bp.route('/clearances/<int:clearance_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_clearance(clearance_id):
    clearance = GateClearance.query.get_or_404(clearance_id)
    clearance.status = 'rejected'
    clearance.approved_by = current_user.id
    clearance.approved_at = datetime.utcnow()
    clearance.notes = request.form.get('notes', 'Rejected by admin')
    db.session.commit()
    flash('Clearance rejected.', 'warning')
    return redirect(url_for('admin.clearances'))


# ── Revenue Monitoring ────────────────────────────────────────────────────────

@admin_bp.route('/revenue')
@login_required
@admin_required
def revenue():
    today = date.today()
    month_start = today.replace(day=1)

    # Monthly totals by gate
    gate_totals = db.session.query(
        Revenue.gate,
        func.sum(Revenue.amount).label('total'),
        func.count(Revenue.id).label('transactions')
    ).filter(Revenue.collected_at >= month_start).group_by(Revenue.gate).all()

    # Daily revenue last 30 days
    daily_revenue = db.session.query(
        func.date(Revenue.collected_at).label('day'),
        func.sum(Revenue.amount).label('total')
    ).filter(
        Revenue.collected_at >= today - timedelta(days=30)
    ).group_by(func.date(Revenue.collected_at)).order_by('day').all()

    # Recent transactions
    page = request.args.get('page', 1, type=int)
    transactions = Revenue.query.order_by(Revenue.collected_at.desc()).paginate(page=page, per_page=20)

    total_month = sum(g.total for g in gate_totals)

    return render_template('admin/revenue.html',
        gate_totals=gate_totals,
        daily_revenue=json.dumps([
            {'day': str(r.day), 'total': float(r.total)} for r in daily_revenue
        ]),
        transactions=transactions,
        total_month=float(total_month),
        month_start=month_start
    )


# ── Wildlife Tracking ─────────────────────────────────────────────────────────

@admin_bp.route('/wildlife')
@login_required
@admin_required
def wildlife():
    sightings = WildlifeSighting.query.order_by(
        WildlifeSighting.sighted_at.desc()
    ).limit(100).all()

    # Species counts
    species_counts = db.session.query(
        WildlifeSighting.species,
        WildlifeSighting.common_name,
        WildlifeSighting.category,
        func.sum(WildlifeSighting.count).label('total')
    ).group_by(
        WildlifeSighting.species,
        WildlifeSighting.common_name,
        WildlifeSighting.category
    ).order_by(func.sum(WildlifeSighting.count).desc()).all()

    # Map data
    map_data = [{
        'id': s.id,
        'species': s.common_name or s.species,
        'category': s.category,
        'count': s.count,
        'lat': float(s.latitude),
        'lng': float(s.longitude),
        'location': s.location_name or '',
        'time': s.sighted_at.strftime('%Y-%m-%d %H:%M'),
        'threat': s.threat_level
    } for s in sightings]

    return render_template('admin/wildlife.html',
        sightings=sightings,
        species_counts=species_counts,
        map_data=json.dumps(map_data)
    )


# ── Vehicle Density ───────────────────────────────────────────────────────────

@admin_bp.route('/vehicles')
@login_required
@admin_required
def vehicles():
    today = date.today()

    # Today's entries by gate
    gate_density = db.session.query(
        GateClearance.gate,
        func.count(GateClearance.id).label('count')
    ).filter(
        func.date(GateClearance.entry_date) == today,
        GateClearance.status == 'approved'
    ).group_by(GateClearance.gate).all()

    # All vehicles
    page = request.args.get('page', 1, type=int)
    vehicles_list = Vehicle.query.order_by(Vehicle.created_at.desc()).paginate(page=page, per_page=20)

    # Hourly density today
    hourly = db.session.query(
        extract('hour', GateClearance.entry_time).label('hour'),
        func.count(GateClearance.id).label('count')
    ).filter(
        func.date(GateClearance.entry_date) == today
    ).group_by('hour').order_by('hour').all()

    return render_template('admin/vehicles.html',
        gate_density=gate_density,
        vehicles=vehicles_list,
        hourly_data=json.dumps([{'hour': int(h.hour or 0), 'count': h.count} for h in hourly])
    )


# ── Reports ───────────────────────────────────────────────────────────────────

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    return render_template('admin/reports.html')


@admin_bp.route('/reports/download')
@login_required
@admin_required
def download_report():
    report_type = request.args.get('type', 'clearances')
    fmt = request.args.get('format', 'pdf')
    date_from = request.args.get('date_from', str(date.today().replace(day=1)))
    date_to = request.args.get('date_to', str(date.today()))

    if fmt == 'pdf':
        filepath = generate_pdf_report(report_type, date_from, date_to)
        return send_file(filepath, as_attachment=True,
                         download_name=f'{report_type}_report_{date_from}_{date_to}.pdf')
    elif fmt == 'excel':
        filepath = generate_excel_report(report_type, date_from, date_to)
        return send_file(filepath, as_attachment=True,
                         download_name=f'{report_type}_report_{date_from}_{date_to}.xlsx')

    flash('Invalid format.', 'danger')
    return redirect(url_for('admin.reports'))


# ── Alerts ────────────────────────────────────────────────────────────────────

@admin_bp.route('/alerts', methods=['GET', 'POST'])
@login_required
@admin_required
def alerts():
    if request.method == 'POST':
        alert = Alert(
            title=request.form.get('title'),
            message=request.form.get('message'),
            alert_type=request.form.get('alert_type', 'info'),
            created_by=current_user.id
        )
        db.session.add(alert)
        db.session.commit()
        flash('Alert created.', 'success')
        return redirect(url_for('admin.alerts'))

    alerts_list = Alert.query.order_by(Alert.created_at.desc()).all()
    return render_template('admin/alerts.html', alerts=alerts_list)


@admin_bp.route('/alerts/<int:alert_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.is_active = not alert.is_active
    db.session.commit()
    return redirect(url_for('admin.alerts'))


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=30)
    return render_template('admin/audit_logs.html', logs=logs)
