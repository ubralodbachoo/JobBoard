import pytest
from app import db
from app.models import User, Job


class TestJobPermissions:
    """Test that users can only edit/delete their own jobs."""
    
    def test_user_can_edit_own_job(self, client, auth, test_user, test_job):
        """Test that a user can edit their own job."""
        auth.login()
        response = client.get(f'/job/{test_job["id"]}/edit')
        assert response.status_code == 200
        assert 'რედაქტირება' in response.data.decode('utf-8')
    
    def test_user_cannot_edit_other_users_job(self, client, auth, test_user, test_user2, test_job, app):
        """Test that a user cannot edit another user's job."""
        # Login as second user
        auth.login(email='test2@example.com', password='testpass123')
        
        # Try to edit first user's job
        response = client.get(f'/job/{test_job["id"]}/edit', follow_redirects=True)
        assert response.status_code == 200
        assert 'არ გაქვთ' in response.data.decode('utf-8') or 'უფლება' in response.data.decode('utf-8')
    
    def test_user_can_delete_own_job(self, client, auth, test_user, test_job, app):
        """Test that a user can delete their own job."""
        auth.login()
        response = client.post(f'/job/{test_job["id"]}/delete', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify job is deleted
        with app.app_context():
            job = Job.query.get(test_job["id"])
            assert job is None
    
    def test_user_cannot_delete_other_users_job(self, client, auth, test_user, test_user2, test_job, app):
        """Test that a user cannot delete another user's job."""
        # Create a job for user2
        with app.app_context():
            user2 = User.query.get(test_user2["id"])
            job2 = Job(
                title='User2 Job',
                short_description='Short desc',
                full_description='Full desc',
                company='Company 2',
                location='Batumi',
                category='Design',
                author=user2
            )
            db.session.add(job2)
            db.session.commit()
            job2_id = job2.id
        
        # Login as first user
        auth.login(email='test@example.com', password='testpass123')
        
        # Try to delete second user's job
        response = client.post(f'/job/{job2_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        assert 'არ გაქვთ' in response.data.decode('utf-8') or 'უფლება' in response.data.decode('utf-8')
        
        # Verify job still exists
        with app.app_context():
            job = Job.query.get(job2_id)
            assert job is not None
    
    def test_unauthorized_user_redirected_from_edit(self, client, test_job):
        """Test that unauthorized user is redirected from edit page."""
        response = client.get(f'/job/{test_job["id"]}/edit')
        assert response.status_code == 302  # Redirect to login
    
    def test_unauthorized_user_redirected_from_delete(self, client, test_job):
        """Test that unauthorized user is redirected from delete route."""
        response = client.post(f'/job/{test_job["id"]}/delete')
        assert response.status_code == 302  # Redirect to login


class TestProfilePermissions:
    """Test profile access permissions."""
    
    def test_user_can_access_own_profile(self, client, auth, test_user):
        """Test that a user can access their own profile."""
        auth.login()
        response = client.get('/profile')
        assert response.status_code == 200
        assert test_user["username"] in response.data.decode('utf-8')
    
    def test_user_can_update_own_profile(self, client, auth, test_user, app):
        """Test that a user can update their own profile."""
        auth.login()
        response = client.post('/profile', data={
            'username': 'updateduser',
            'email': test_user["email"]
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify username was updated
        with app.app_context():
            user = User.query.get(test_user["id"])
            assert user.username == 'updateduser'
    
    def test_unauthorized_user_cannot_access_profile(self, client):
        """Test that unauthorized user cannot access profile page."""
        response = client.get('/profile')
        assert response.status_code == 302  # Redirect to login


class TestJobVisibility:
    """Test job visibility for different users."""
    
    def test_all_users_can_view_jobs(self, client, test_job):
        """Test that anyone can view job listings (no login required)."""
        response = client.get('/')
        assert response.status_code == 200
        assert test_job["title"] in response.data.decode('utf-8')
    
    def test_all_users_can_view_job_detail(self, client, test_job):
        """Test that anyone can view job details (no login required)."""
        response = client.get(f'/job/{test_job["id"]}')
        assert response.status_code == 200
        assert test_job["title"] in response.data.decode('utf-8')
    
    def test_edit_delete_buttons_only_for_author(self, client, auth, test_user, test_user2, test_job):
        """Test that edit/delete buttons only appear for job author."""
        # View job without login - no edit/delete buttons
        response = client.get(f'/job/{test_job["id"]}')
        assert response.status_code == 200
        assert 'რედაქტირება' not in response.data.decode('utf-8') or 'edit' not in response.data.decode('utf-8').lower()
        
        # Login as job author - should see edit/delete buttons
        auth.login()
        response = client.get(f'/job/{test_job["id"]}')
        assert response.status_code == 200
        assert 'რედაქტირება' in response.data.decode('utf-8')
        
        # Logout and login as different user - no edit/delete buttons
        auth.logout()
        auth.login(email='test2@example.com', password='testpass123')
        response = client.get(f'/job/{test_job["id"]}')
        assert response.status_code == 200
        # Edit button should not appear or should be hidden for non-authors


class TestUserJobsPage:
    """Test user jobs page permissions."""
    
    def test_anyone_can_view_user_jobs(self, client, test_user, test_job):
        """Test that anyone can view a user's job listings."""
        response = client.get(f'/user/{test_user["username"]}')
        assert response.status_code == 200
        assert test_user["username"] in response.data.decode('utf-8')
        assert test_job["title"] in response.data.decode('utf-8')
    
    def test_user_jobs_page_shows_only_user_jobs(self, client, test_user, test_user2, test_job, app):
        """Test that user jobs page only shows that user's jobs."""
        # Create job for user2
        with app.app_context():
            user2 = User.query.get(test_user2["id"])
            job2 = Job(
                title='User2 Exclusive Job',
                short_description='Short desc',
                full_description='Full desc',
                company='Company 2',
                location='Batumi',
                category='Marketing',
                author=user2
            )
            db.session.add(job2)
            db.session.commit()
        
        # Check user1's jobs page - should not see user2's job
        response = client.get(f'/user/{test_user["username"]}')
        assert response.status_code == 200
        assert test_job["title"] in response.data.decode('utf-8')
        assert 'User2 Exclusive Job' not in response.data.decode('utf-8')
        
        # Check user2's jobs page - should see user2's job
        response = client.get(f'/user/{test_user2["username"]}')
        assert response.status_code == 200
        assert 'User2 Exclusive Job' in response.data.decode('utf-8')
        assert test_job["title"] not in response.data.decode('utf-8')

