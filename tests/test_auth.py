import pytest
from app import db
from app.models import User


class TestRegistration:
    """Test user registration functionality."""
    
    def test_register_page_loads(self, client):
        """Test that registration page loads."""
        response = client.get('/register')
        assert response.status_code == 200
        assert 'რეგისტრაცია' in response.data.decode('utf-8')
    
    def test_successful_registration(self, client, app):
        """Test successful user registration."""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'წარმატებით დარეგისტრირდით' in response.data.decode('utf-8')
        
        # Check that user was created in database
        with app.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.username == 'newuser'
    
    def test_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'different@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'სახელი უკვე გამოყენებულია' in response.data.decode('utf-8')
    
    def test_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        response = client.post('/register', data={
            'username': 'differentuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'ელფოსტა უკვე დარეგისტრირებულია' in response.data.decode('utf-8')
    
    def test_password_mismatch(self, client):
        """Test registration with mismatched passwords."""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'different123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'პაროლები არ ემთხვევა' in response.data.decode('utf-8')
    
    def test_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'ელფოსტის ფორმატი' in response.data.decode('utf-8')


class TestLogin:
    """Test user login functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads."""
        response = client.get('/login')
        assert response.status_code == 200
        assert 'შესვლა' in response.data.decode('utf-8')
    
    def test_successful_login(self, client, test_user):
        """Test successful login."""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpass123',
            'remember_me': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'წარმატებით შეხვედით' in response.data.decode('utf-8')
    
    def test_login_with_wrong_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword',
            'remember_me': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'არასწორი ელფოსტა ან პაროლი' in response.data.decode('utf-8')
    
    def test_login_with_nonexistent_email(self, client):
        """Test login with non-existent email."""
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123',
            'remember_me': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'არასწორი ელფოსტა ან პაროლი' in response.data.decode('utf-8')
    
    def test_login_redirect_when_authenticated(self, client, auth, test_user):
        """Test that logged in user is redirected from login page."""
        auth.login()
        response = client.get('/login')
        assert response.status_code == 302  # Redirect to index


class TestLogout:
    """Test user logout functionality."""
    
    def test_logout(self, client, auth, test_user):
        """Test logout functionality."""
        auth.login()
        response = auth.logout()
        
        assert response.status_code == 200
        assert 'წარმატებით გამოხვედით' in response.data.decode('utf-8')
    
    def test_logout_redirects_to_index(self, client, auth, test_user):
        """Test that logout redirects to index page."""
        auth.login()
        response = client.get('/logout', follow_redirects=False)
        assert response.status_code == 302
        assert response.location.endswith('/') or response.location.endswith('/index')


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_is_hashed(self, app):
        """Test that passwords are hashed and not stored as plain text."""
        with app.app_context():
            user = User(username='hashtest', email='hash@example.com')
            user.set_password('mypassword')
            db.session.add(user)
            db.session.commit()
            
            # Password hash should not equal the plain password
            assert user.password_hash != 'mypassword'
            # Check password should return True
            assert user.check_password('mypassword') is True
            # Wrong password should return False
            assert user.check_password('wrongpassword') is False


class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    def test_register_login_logout_flow(self, client, auth):
        """Test complete registration, login, and logout flow."""
        # Register
        response = auth.register(
            username='flowtest',
            email='flow@example.com',
            password='password123'
        )
        assert response.status_code == 200
        
        # Login
        response = auth.login(email='flow@example.com', password='password123')
        assert response.status_code == 200
        
        # Logout
        response = auth.logout()
        assert response.status_code == 200
    
    def test_authenticated_user_can_access_protected_routes(self, client, auth, test_user):
        """Test that authenticated users can access protected routes."""
        # Try to access protected route without login
        response = client.get('/add-job')
        assert response.status_code == 302
        
        # Login
        auth.login()
        
        # Now should be able to access protected route
        response = client.get('/add-job')
        assert response.status_code == 200

