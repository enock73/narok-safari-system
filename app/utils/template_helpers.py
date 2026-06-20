"""
Template helpers: filters and context processors.
Import and register this in create_app().
"""
from datetime import date


def register_template_helpers(app):
    """Register custom Jinja2 filters and context processors."""

    @app.template_filter('currency')
    def currency_filter(value, symbol='KES'):
        try:
            return f"{symbol} {float(value):,.0f}"
        except (ValueError, TypeError):
            return f"{symbol} 0"

    @app.template_filter('dateformat')
    def dateformat_filter(value, fmt='%d %b %Y'):
        if value is None:
            return '—'
        try:
            return value.strftime(fmt)
        except AttributeError:
            return str(value)

    @app.template_filter('timeago')
    def timeago_filter(value):
        from datetime import datetime
        if value is None:
            return '—'
        now = datetime.utcnow()
        diff = now - value
        seconds = diff.total_seconds()
        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            mins = int(seconds / 60)
            return f'{mins} min{"s" if mins > 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        else:
            days = diff.days
            return f'{days} day{"s" if days > 1 else ""} ago'

    @app.context_processor
    def inject_globals():
        return {
            'today': date.today(),
            'now_month': date.today().replace(day=1).isoformat(),
            'now_today': date.today().isoformat(),
        }
