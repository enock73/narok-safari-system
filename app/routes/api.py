from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import (GateClearance, WildlifeSighting, Vehicle,
                         User, Revenue, Alert)
from datetime import datetime, date, timedelta
from sqlalchemy import func
from functools import wraps

api_bp = Blueprint('api', __name__)


def api_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if not current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


# ── Wildlife Map Data ─────────────────────────────────────────────────────────

@api_bp.route('/wildlife/map')
@login_required
def wildlife_map():
    days = request.args.get('days', 7, type=int)
    category = request.args.get('category', '')
    since = datetime.utcnow() - timedelta(days=days)

    query = WildlifeSighting.query.filter(WildlifeSighting.sighted_at >= since)
    if category:
        query = query.filter_by(category=category)

    sightings = query.all()
    data = [{
        'id': s.id,
        'species': s.common_name or s.species,
        'scientific': s.species,
        'category': s.category,
        'count': s.count,
        'lat': float(s.latitude),
        'lng': float(s.longitude),
        'location': s.location_name or '',
        'behavior': s.behavior,
        'time': s.sighted_at.strftime('%Y-%m-%d %H:%M'),
        'threat': s.threat_level,
        'verified': s.is_verified,
        'photos': [p.filename for p in s.photos]
    } for s in sightings]
    return jsonify({'sightings': data, 'count': len(data)})


@api_bp.route('/wildlife/stats')
@login_required
def wildlife_stats():
    today = date.today()
    by_category = db.session.query(
        WildlifeSighting.category,
        func.count(WildlifeSighting.id).label('reports'),
        func.sum(WildlifeSighting.count).label('total')
    ).group_by(WildlifeSighting.category).all()

    return jsonify({
        'by_category': [
            {'category': r.category, 'reports': r.reports, 'total': int(r.total or 0)}
            for r in by_category
        ]
    })


# ── Clearance Status ──────────────────────────────────────────────────────────

@api_bp.route('/clearance/<token>/status')
def clearance_status(token):
    clearance = GateClearance.query.filter_by(token=token).first()
    if not clearance:
        return jsonify({'error': 'Invalid token'}), 404

    return jsonify({
        'token': clearance.token,
        'status': clearance.status,
        'gate': clearance.gate,
        'guide': clearance.guide.full_name,
        'vehicle': clearance.vehicle.plate_number,
        'entry_date': str(clearance.entry_date),
        'passenger_count': clearance.passenger_count,
        'purpose': clearance.purpose,
        'approved_at': clearance.approved_at.isoformat() if clearance.approved_at else None
    })


# ── Dashboard Stats ───────────────────────────────────────────────────────────

@api_bp.route('/dashboard/stats')
@login_required
@api_admin_required
def dashboard_stats():
    today = date.today()

    return jsonify({
        'today': {
            'clearances': GateClearance.query.filter(
                func.date(GateClearance.entry_date) == today
            ).count(),
            'sightings': WildlifeSighting.query.filter(
                func.date(WildlifeSighting.sighted_at) == today
            ).count(),
            'revenue': float(db.session.query(func.sum(Revenue.amount)).filter(
                func.date(Revenue.collected_at) == today
            ).scalar() or 0)
        },
        'pending_clearances': GateClearance.query.filter_by(status='pending').count(),
        'active_guides': User.query.filter_by(role='guide', is_active=True).count(),
        'total_vehicles': Vehicle.query.filter_by(is_active=True).count()
    })


# ── Gate Vehicle Counts ───────────────────────────────────────────────────────

@api_bp.route('/gates/density')
@login_required
def gates_density():
    today = date.today()
    gate_data = db.session.query(
        GateClearance.gate,
        func.count(GateClearance.id).label('count')
    ).filter(
        func.date(GateClearance.entry_date) == today,
        GateClearance.status == 'approved'
    ).group_by(GateClearance.gate).all()

    gates = {
        'Sekenani Gate':    {'lat': -1.5667, 'lng': 35.1833},
        'Oloololo Gate':    {'lat': -1.4000, 'lng': 35.0000},
        'Talek Gate':       {'lat': -1.6667, 'lng': 35.2167},
        'Musiara Gate':     {'lat': -1.3833, 'lng': 35.0333},
        'Sand River Gate':  {'lat': -1.6500, 'lng': 35.3333},
        'Ololaimutia Gate': {'lat': -1.6167, 'lng': 35.1500},
    }
    result = []
    counts = {g.gate: g.count for g in gate_data}
    for name, coords in gates.items():
        result.append({
            'name': name,
            'lat': coords['lat'],
            'lng': coords['lng'],
            'count': counts.get(name, 0)
        })
    return jsonify({'gates': result})


# ── Revenue Chart Data ────────────────────────────────────────────────────────

@api_bp.route('/revenue/chart')
@login_required
@api_admin_required
def revenue_chart():
    days = request.args.get('days', 30, type=int)
    since = date.today() - timedelta(days=days)

    daily = db.session.query(
        func.date(Revenue.collected_at).label('day'),
        func.sum(Revenue.amount).label('total')
    ).filter(Revenue.collected_at >= since).group_by(
        func.date(Revenue.collected_at)
    ).order_by('day').all()

    return jsonify({
        'labels': [str(r.day) for r in daily],
        'data': [float(r.total) for r in daily]
    })


# ── Alerts ────────────────────────────────────────────────────────────────────

@api_bp.route('/alerts/active')
@login_required
def active_alerts():
    alerts = Alert.query.filter_by(is_active=True).order_by(
        Alert.created_at.desc()
    ).limit(10).all()
    return jsonify({'alerts': [
        {'id': a.id, 'title': a.title, 'message': a.message,
         'type': a.alert_type, 'created': a.created_at.isoformat()}
        for a in alerts
    ]})


# ── Guide: My Vehicles ────────────────────────────────────────────────────────

@api_bp.route('/guide/vehicles')
@login_required
def guide_vehicles():
    if current_user.is_admin():
        return jsonify({'error': 'Guide endpoint only'}), 403
    vehicles = Vehicle.query.filter_by(user_id=current_user.id, is_active=True).all()
    return jsonify({'vehicles': [
        {'id': v.id, 'plate': v.plate_number, 'type': v.vehicle_type,
         'capacity': v.capacity}
        for v in vehicles
    ]})
