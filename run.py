"""
run.py — Application entry point.
Usage:
    python run.py
    flask run --host=0.0.0.0 --port=5000
"""
import os
from app import create_app, db
from app.models import User, Vehicle, GateClearance, WildlifeSighting, Revenue

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Vehicle': Vehicle,
        'GateClearance': GateClearance,
        'WildlifeSighting': WildlifeSighting,
        'Revenue': Revenue,
    }


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
