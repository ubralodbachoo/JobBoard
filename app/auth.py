from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        current_app.logger.info(f'New user registered: {user.username} ({user.email})')
        flash('გილოცავთ! თქვენ წარმატებით დარეგისტრირდით. ახლა შეგიძლიათ შესვლა.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', title='რეგისტრაცია', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            current_app.logger.warning(f'Failed login attempt for email: {form.email.data}')
            flash('არასწორი ელფოსტა ან პაროლი.', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        current_app.logger.info(f'User logged in: {user.username} ({user.email})')
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        flash(f'გამარჯობა, {user.username}! თქვენ წარმატებით შეხვედით სისტემაში.', 'success')
        return redirect(next_page)
    
    return render_template('login.html', title='შესვლა', form=form)


@bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        current_app.logger.info(f'User logged out: {current_user.username}')
    logout_user()
    flash('თქვენ წარმატებით გამოხვედით სისტემიდან.', 'info')
    return redirect(url_for('main.index'))

