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

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    if not app.logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        if os.environ.get('VERCEL'):
            handler = logging.StreamHandler()
        elif app.debug:
            handler = logging.FileHandler('app.log', encoding='utf-8')
        else:
            handler = RotatingFileHandler(
                'app.log', maxBytes=10 * 1024 * 1024, backupCount=10, encoding='utf-8'
            )
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

    return app
