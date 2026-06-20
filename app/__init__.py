from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure upload directories exist
    for folder in [
        app.config['UPLOAD_FOLDER'],
        app.config['PHOTO_FOLDER'],
        app.config['MANIFEST_FOLDER'],
        app.config['QR_FOLDER'],
    ]:
        os.makedirs(folder, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Register template helpers
    from app.utils.template_helpers import register_template_helpers
    register_template_helpers(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.guide import guide_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(guide_bp, url_prefix='/guide')
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from app.routes.tourist import tourist_bp
    app.register_blueprint(tourist_bp, url_prefix='/safari')

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('shared/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('shared/500.html'), 500

    return app
