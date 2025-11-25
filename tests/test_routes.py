import pytest
from app import db
from app.models import Job


class TestPublicRoutes:
    """Test public routes that don't require authentication."""
    
    def test_index_route(self, client):
        """Test the main index page."""
        response = client.get('/')
        assert response.status_code == 200
        assert 'ვაკანსიები' in response.data.decode('utf-8')
    
    def test_index_route_alternative(self, client):
        """Test the /index route."""
        response = client.get('/index')
        assert response.status_code == 200
    
    def test_about_route(self, client):
        """Test the about page."""
        response = client.get('/about')
        assert response.status_code == 200
        assert 'ჩვენ შესახებ' in response.data.decode('utf-8')
    
    def test_job_detail_route(self, client, test_job):
        """Test job detail page."""
        response = client.get(f'/job/{test_job["id"]}')
        assert response.status_code == 200
        assert test_job["title"] in response.data.decode('utf-8')
    
    def test_job_detail_not_found(self, client):
        """Test job detail page with invalid ID."""
        response = client.get('/job/9999')
        assert response.status_code == 404
    
    def test_user_jobs_route(self, client, test_user, test_job):
        """Test user jobs page."""
        response = client.get(f'/user/{test_user["username"]}')
        assert response.status_code == 200
        assert test_user["username"] in response.data.decode('utf-8')
    
    def test_user_jobs_not_found(self, client):
        """Test user jobs page with invalid username."""
        response = client.get('/user/nonexistentuser')
        assert response.status_code == 404


class TestProtectedRoutes:
    """Test routes that require authentication."""
    
    def test_add_job_requires_login(self, client):
        """Test that add job page requires login."""
        response = client.get('/add-job')
        assert response.status_code == 302  # Redirect to login
    
    def test_edit_job_requires_login(self, client, test_job):
        """Test that edit job page requires login."""
        response = client.get(f'/job/{test_job["id"]}/edit')
        assert response.status_code == 302  # Redirect to login
    
    def test_profile_requires_login(self, client):
        """Test that profile page requires login."""
        response = client.get('/profile')
        assert response.status_code == 302  # Redirect to login
    
    def test_add_job_page_with_login(self, client, auth, test_user):
        """Test that logged in user can access add job page."""
        auth.login()
        response = client.get('/add-job')
        assert response.status_code == 200
        assert 'ვაკანსიის დამატება' in response.data.decode('utf-8')
    
    def test_profile_page_with_login(self, client, auth, test_user):
        """Test that logged in user can access profile page."""
        auth.login()
        response = client.get('/profile')
        assert response.status_code == 200
        assert 'პროფილი' in response.data.decode('utf-8')


class TestJobCRUD:
    """Test CRUD operations for jobs."""
    
    def test_create_job(self, client, auth, test_user, app):
        """Test creating a new job."""
        auth.login()
        response = client.post('/add-job', data={
            'title': 'New Job',
            'short_description': 'Short description of the job',
            'full_description': 'Full description of the job',
            'company': 'New Company',
            'salary': '2000-3000',
            'location': 'Batumi',
            'category': 'IT'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that job was created in database
        with app.app_context():
            job = Job.query.filter_by(title='New Job').first()
            assert job is not None
            assert job.company == 'New Company'
    
    def test_edit_job(self, client, auth, test_user, test_job, app):
        """Test editing a job."""
        auth.login()
        response = client.post(f'/job/{test_job["id"]}/edit', data={
            'title': 'Updated Job Title',
            'short_description': 'This is a test job description',
            'full_description': 'This is the full description of the test job',
            'company': 'Test Company',
            'salary': '1000-2000',
            'location': 'Tbilisi',
            'category': 'IT'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that job was updated in database
        with app.app_context():
            job = Job.query.get(test_job["id"])
            assert job.title == 'Updated Job Title'
    
    def test_delete_job(self, client, auth, test_user, test_job, app):
        """Test deleting a job."""
        auth.login()
        response = client.post(f'/job/{test_job["id"]}/delete', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that job was deleted from database
        with app.app_context():
            job = Job.query.get(test_job["id"])
            assert job is None


class TestPagination:
    """Test pagination functionality."""
    
    def test_pagination_on_index(self, client, test_user, app):
        """Test pagination on index page."""
        # Create multiple jobs
        with app.app_context():
            for i in range(15):
                job = Job(
                    title=f'Job {i}',
                    short_description='Short desc',
                    full_description='Full desc',
                    company='Company',
                    location='Tbilisi',
                    category='IT',
                    author_id=test_user['id']
                )
                db.session.add(job)
            db.session.commit()
        
        # Test first page
        response = client.get('/')
        assert response.status_code == 200
        
        # Test second page
        response = client.get('/?page=2')
        assert response.status_code == 200


class TestAccountDeletion:
    """Test account deletion functionality."""
    
    def test_delete_account_requires_login(self, client):
        """Test that delete account requires login."""
        response = client.post('/delete-account')
        assert response.status_code == 302  # Redirect to login
    
    def test_delete_account_with_wrong_password(self, client, auth, test_user):
        """Test account deletion with wrong password."""
        auth.login()
        response = client.post('/delete-account', data={
            'password': 'wrongpassword',
            'confirm_delete': 'DELETE'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'არასწორი პაროლი' in response.data.decode('utf-8')
    
    def test_delete_account_without_confirmation(self, client, auth, test_user):
        """Test account deletion without DELETE confirmation."""
        auth.login()
        response = client.post('/delete-account', data={
            'password': 'testpass123',
            'confirm_delete': 'WRONG'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'DELETE' in response.data.decode('utf-8')
    
    def test_delete_account_successful(self, client, auth, test_user, test_job, app):
        """Test successful account deletion."""
        auth.login()
        
        # Verify user and job exist before deletion
        with app.app_context():
            from app.models import User
            user = User.query.get(test_user['id'])
            assert user is not None
            job = Job.query.get(test_job['id'])
            assert job is not None
        
        # Delete account
        response = client.post('/delete-account', data={
            'password': 'testpass123',
            'confirm_delete': 'DELETE'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'ანგარიში და ყველა ვაკანსია წარმატებით წაიშალა' in response.data.decode('utf-8')
        
        # Verify user and jobs were deleted (cascade)
        with app.app_context():
            from app.models import User
            user = User.query.get(test_user['id'])
            assert user is None
            job = Job.query.get(test_job['id'])
            assert job is None

