from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from . import users_bp
from models.models import User
from .forms import LoginForm

@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Неверные имя пользователя или пароль')
    return render_template('users/login.html', form=form)

@users_bp.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    # После выхода возвращаем на главную страницу
    return redirect(url_for('main.index'))