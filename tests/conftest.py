import pytest
import os
import tempfile
from app import create_app, db
from app.models import User, Job
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def auth(client):
    """Authentication helper."""
    class AuthActions:
        def __init__(self, client):
            self._client = client
        
        def register(self, username='testuser', email='test@example.com', password='testpass123'):
            return self._client.post(
                '/register',
                data={
                    'username': username,
                    'email': email,
                    'password': password,
                    'confirm_password': password
                },
                follow_redirects=True
            )
        
        def login(self, email='test@example.com', password='testpass123'):
            return self._client.post(
                '/login',
                data={'email': email, 'password': password},
                follow_redirects=True
            )
        
        def logout(self):
            return self._client.get('/logout', follow_redirects=True)
    
    return AuthActions(client)


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        db.session.expunge(user)  # Detach from session
    
    # Return a dict with user info instead of the object
    return {'id': user_id, 'username': 'testuser', 'email': 'test@example.com'}


@pytest.fixture
def test_user2(app):
    """Create a second test user."""
    with app.app_context():
        user = User(username='testuser2', email='test2@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        db.session.expunge(user)  # Detach from session
    
    # Return a dict with user info instead of the object
    return {'id': user_id, 'username': 'testuser2', 'email': 'test2@example.com'}


@pytest.fixture
def test_job(app, test_user):
    """Create a test job."""
    with app.app_context():
        job = Job(
            title='Test Job',
            short_description='This is a test job description',
            full_description='This is the full description of the test job',
            company='Test Company',
            salary='1000-2000',
            location='Tbilisi',
            category='IT',
            author_id=test_user['id']  # Use dict key instead
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id
        db.session.expunge(job)  # Detach from session
    
    # Return a dict with job info
    return {'id': job_id, 'title': 'Test Job'}

