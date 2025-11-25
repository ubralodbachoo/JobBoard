import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'გთხოვთ, შეხვიდეთ სისტემაში ამ გვერდის სანახავად.'
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Set up logging (avoid duplicate handlers)
    if not app.logger.handlers:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Use simple FileHandler in debug mode to avoid Windows rotation issues
        if app.debug:
            file_handler = logging.FileHandler('app.log', encoding='utf-8')
        else:
            # Use RotatingFileHandler in production
            file_handler = RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=10, encoding='utf-8')
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('JobBoard startup')

    # Error handlers
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    return app


