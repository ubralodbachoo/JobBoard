import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, logout_user
from app import db
from app.models import User, Job
from app.forms import JobForm, ProfileUpdateForm, DeleteAccountForm
from app.api_integration import search_adzuna_jobs

bp = Blueprint('main', __name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_picture(form_picture):
    """Save uploaded profile picture and return filename"""
    random_hex = os.urandom(8).hex()
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_fn)
    
    # Save the image
    form_picture.save(picture_path)
    
    return picture_fn


@bp.route('/')
@bp.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    jobs_pagination = Job.query.order_by(Job.date_posted.desc()).paginate(
        page=page, per_page=9, error_out=False)
    return render_template('index.html', title='ვაკანსიები', jobs=jobs_pagination)


@bp.route('/about')
def about():
    """About page with real statistics from database"""
    # რეალური სტატისტიკა ბაზიდან
    total_jobs = Job.query.count()
    total_users = User.query.count()
    
    stats = {
        'total_jobs': total_jobs,
        'total_users': total_users
    }
    
    return render_template('about.html', title='ჩვენ შესახებ', stats=stats)


@bp.route('/explore-jobs')
def explore_jobs():
    """Explore real jobs from Adzuna API"""
    query = request.args.get('q', '')
    location = request.args.get('location', '')
    country = request.args.get('country', 'gb')
    page = request.args.get('page', 1, type=int)
    
    adzuna_data = search_adzuna_jobs(query=query, location=location, page=page, country=country)
    
    if adzuna_data:
        return render_template('explore_jobs.html', 
                             title='რეალური ვაკანსიები', 
                             data=adzuna_data,
                             query=query,
                             location=location,
                             country=country)
    else:
        flash('ვაკანსიების ძიებისას მოხდა შეცდომა. გთხოვთ სცადოთ მოგვიანებით.', 'warning')
        return render_template('explore_jobs.html', 
                             title='რეალური ვაკანსიები', 
                             data=None,
                             query=query,
                             location=location,
                             country=country)


@bp.route('/job/<int:id>')
def job_detail(id):
    job = Job.query.get_or_404(id)
    return render_template('job_detail.html', title=job.title, job=job)


@bp.route('/add-job', methods=['GET', 'POST'])
@login_required
def add_job():
    form = JobForm()
    if form.validate_on_submit():
        job = Job(
            title=form.title.data,
            short_description=form.short_description.data,
            full_description=form.full_description.data,
            company=form.company.data,
            salary=form.salary.data,
            location=form.location.data,
            category=form.category.data,
            author=current_user
        )
        db.session.add(job)
        db.session.commit()
        
        current_app.logger.info(f'Job created: "{job.title}" by user {current_user.username}')
        flash('ვაკანსია წარმატებით დაემატა!', 'success')
        return redirect(url_for('main.job_detail', id=job.id))
    
    return render_template('add_job.html', title='ვაკანსიის დამატება', form=form)


@bp.route('/job/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(id):
    job = Job.query.get_or_404(id)
    
    # Check if current user is the author
    if job.author != current_user:
        flash('თქვენ არ გაქვთ ამ ვაკანსიის რედაქტირების უფლება.', 'danger')
        current_app.logger.warning(
            f'Unauthorized edit attempt: User {current_user.username} tried to edit job {id}'
        )
        return redirect(url_for('main.job_detail', id=job.id))
    
    form = JobForm()
    if form.validate_on_submit():
        job.title = form.title.data
        job.short_description = form.short_description.data
        job.full_description = form.full_description.data
        job.company = form.company.data
        job.salary = form.salary.data
        job.location = form.location.data
        job.category = form.category.data
        db.session.commit()
        
        current_app.logger.info(f'Job edited: ID {job.id} by user {current_user.username}')
        flash('ვაკანსია წარმატებით განახლდა!', 'success')
        return redirect(url_for('main.job_detail', id=job.id))
    
    elif request.method == 'GET':
        form.title.data = job.title
        form.short_description.data = job.short_description
        form.full_description.data = job.full_description
        form.company.data = job.company
        form.salary.data = job.salary
        form.location.data = job.location
        form.category.data = job.category
    
    return render_template('edit_job.html', title='ვაკანსიის რედაქტირება', form=form, job=job)


@bp.route('/job/<int:id>/delete', methods=['POST'])
@login_required
def delete_job(id):
    job = Job.query.get_or_404(id)
    
    # Check if current user is the author
    if job.author != current_user:
        flash('თქვენ არ გაქვთ ამ ვაკანსიის წაშლის უფლება.', 'danger')
        current_app.logger.warning(
            f'Unauthorized delete attempt: User {current_user.username} tried to delete job {id}'
        )
        return redirect(url_for('main.job_detail', id=job.id))
    
    db.session.delete(job)
    db.session.commit()
    
    current_app.logger.info(f'Job deleted: ID {id} by user {current_user.username}')
    flash('ვაკანსია წარმატებით წაიშალა.', 'success')
    return redirect(url_for('main.index'))


@bp.route('/user/<username>')
def user_jobs(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    jobs = Job.query.filter_by(author=user).order_by(Job.date_posted.desc()).paginate(
        page=page, per_page=9, error_out=False)
    return render_template('user_jobs.html', title=f'{user.username}-ის ვაკანსიები', 
                          user=user, jobs=jobs)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileUpdateForm(current_user.username, current_user.email)
    delete_form = DeleteAccountForm()
    
    if form.validate_on_submit():
        if form.profile_picture.data:
            picture_file = save_picture(form.profile_picture.data)
            current_user.profile_image = picture_file
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        
        current_app.logger.info(f'Profile updated: {current_user.username}')
        flash('თქვენი პროფილი წარმატებით განახლდა!', 'success')
        return redirect(url_for('main.profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    # Get user's profile image
    image_file = url_for('static', filename='uploads/' + current_user.profile_image)
    
    return render_template('profile.html', title='პროფილი', form=form, 
                          image_file=image_file, delete_form=delete_form)


@bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    
    if form.validate_on_submit():
        # Verify password
        if not current_user.check_password(form.password.data):
            flash('არასწორი პაროლი. გთხოვთ სცადოთ თავიდან.', 'danger')
            return redirect(url_for('main.profile'))
        
        # Verify DELETE confirmation
        if form.confirm_delete.data.strip().upper() != 'DELETE':
            flash('გთხოვთ ჩაწეროთ "DELETE" ანგარიშის წასაშლელად.', 'danger')
            return redirect(url_for('main.profile'))
        
        # Store username for logging before deletion
        username = current_user.username
        user_id = current_user.id
        jobs_count = current_user.jobs.count()
        
        # Delete user profile image if not default
        if current_user.profile_image != 'default.jpg':
            try:
                profile_pic_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_image)
                if os.path.exists(profile_pic_path):
                    os.remove(profile_pic_path)
            except Exception as e:
                current_app.logger.error(f'Error deleting profile image: {str(e)}')
        
        # Logout user
        logout_user()
        
        # Delete user (cascade will delete all jobs automatically)
        user = User.query.get(user_id)
        db.session.delete(user)
        db.session.commit()
        
        current_app.logger.info(
            f'Account deleted: User {username} (ID: {user_id}) and {jobs_count} jobs'
        )
        flash('თქვენი ანგარიში და ყველა ვაკანსია წარმატებით წაიშალა.', 'info')
        return redirect(url_for('main.index'))
    
    flash('ანგარიშის წაშლა ვერ მოხერხდა. გთხოვთ სცადოთ თავიდან.', 'danger')
    return redirect(url_for('main.profile'))

