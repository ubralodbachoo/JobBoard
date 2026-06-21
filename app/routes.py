from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from app import db
from app.models import User, Job
from app.forms import JobForm, ProfileUpdateForm, DeleteAccountForm
from app.api_integration import search_adzuna_jobs

bp = Blueprint('main', __name__)


def _author_required(job):
    if job.author != current_user:
        flash('თქვენ არ გაქვთ ამ ვაკანსიაზე საჭირო უფლება.', 'danger')
        return False
    return True


@bp.route('/')
@bp.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    jobs = Job.query.order_by(Job.date_posted.desc()).paginate(
        page=page, per_page=9, error_out=False
    )
    return render_template('index.html', title='ვაკანსიები', jobs=jobs)


@bp.route('/about')
def about():
    return render_template(
        'about.html',
        title='ჩვენ შესახებ',
        stats={'total_jobs': Job.query.count(), 'total_users': User.query.count()},
    )


@bp.route('/explore-jobs')
def explore_jobs():
    query = request.args.get('q', '')
    location = request.args.get('location', '')
    country = request.args.get('country', 'gb')
    page = request.args.get('page', 1, type=int)

    data = search_adzuna_jobs(query=query, location=location, page=page, country=country)
    if data is None:
        flash('ვაკანსიების ძიებისას მოხდა შეცდომა. გთხოვთ სცადოთ მოგვიანებით.', 'warning')

    return render_template(
        'explore_jobs.html',
        title='რეალური ვაკანსიები',
        data=data,
        query=query,
        location=location,
        country=country,
    )


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
            author=current_user,
        )
        db.session.add(job)
        db.session.commit()
        flash('ვაკანსია წარმატებით დაემატა!', 'success')
        return redirect(url_for('main.job_detail', id=job.id))
    return render_template('add_job.html', title='ვაკანსიის დამატება', form=form)


@bp.route('/job/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(id):
    job = Job.query.get_or_404(id)
    if not _author_required(job):
        return redirect(url_for('main.job_detail', id=job.id))

    form = JobForm()
    if form.validate_on_submit():
        form.populate_obj(job)
        db.session.commit()
        flash('ვაკანსია წარმატებით განახლდა!', 'success')
        return redirect(url_for('main.job_detail', id=job.id))
    if request.method == 'GET':
        form = JobForm(obj=job)
    return render_template('edit_job.html', title='ვაკანსიის რედაქტირება', form=form, job=job)


@bp.route('/job/<int:id>/delete', methods=['POST'])
@login_required
def delete_job(id):
    job = Job.query.get_or_404(id)
    if not _author_required(job):
        return redirect(url_for('main.job_detail', id=job.id))

    db.session.delete(job)
    db.session.commit()
    flash('ვაკანსია წარმატებით წაიშალა.', 'success')
    return redirect(url_for('main.index'))


@bp.route('/user/<username>')
def user_jobs(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    jobs = Job.query.filter_by(author=user).order_by(Job.date_posted.desc()).paginate(
        page=page, per_page=9, error_out=False
    )
    return render_template(
        'user_jobs.html',
        title=f'{user.username}-ის ვაკანსიები',
        user=user,
        jobs=jobs,
    )


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileUpdateForm(current_user.username, current_user.email)
    delete_form = DeleteAccountForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('თქვენი პროფილი წარმატებით განახლდა!', 'success')
        return redirect(url_for('main.profile'))

    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template(
        'profile.html',
        title='პროფილი',
        form=form,
        delete_form=delete_form,
    )


@bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if not form.validate_on_submit():
        flash('ანგარიშის წაშლა ვერ მოხერხდა.', 'danger')
        return redirect(url_for('main.profile'))

    if not current_user.check_password(form.password.data):
        flash('არასწორი პაროლი.', 'danger')
        return redirect(url_for('main.profile'))

    if form.confirm_delete.data.strip().upper() != 'DELETE':
        flash('გთხოვთ ჩაწეროთ "DELETE".', 'danger')
        return redirect(url_for('main.profile'))

    user_id = current_user.id
    logout_user()
    db.session.delete(User.query.get(user_id))
    db.session.commit()
    flash('ანგარიში წაიშალა.', 'info')
    return redirect(url_for('main.index'))
