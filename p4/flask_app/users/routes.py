from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_required, login_user, logout_user
import base64
from io import BytesIO
from .. import bcrypt
from werkzeug.utils import secure_filename
from ..forms import RegistrationForm, LoginForm, UpdateUsernameForm, UpdateProfilePicForm
from ..models import User

users = Blueprint("users", __name__)

""" ************ User Management views ************ """


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('movies.index'))
    
    registration_form = RegistrationForm()
    
    if registration_form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(registration_form.password.data).decode('utf-8')
        new_user = User(username=registration_form.username.data, 
                        email=registration_form.email.data,
                        password=hashed_password)
        new_user.save()
        return redirect(url_for('users.login'))

    return render_template('register.html', form=registration_form)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('movies.index'))
    
    login_form = LoginForm()

    if login_form.validate_on_submit():
        user = User.objects(username=login_form.username.data).first()

        if (user is not None) and (bcrypt.check_password_hash(user.password, login_form.password.data)):
            login_user(user)
            return redirect(url_for('users.account'))
        else:
            flash('Incorrect username or password. Please try again.')
    
    return render_template('login.html', form=login_form)


@users.route("/logout")
@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()

        return redirect(url_for('movies.index'))


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    update_username_form = UpdateUsernameForm()
    update_profile_pic_form = UpdateProfilePicForm()
    image = None
    if request.method == "POST":
        if update_username_form.submit_username.data and update_username_form.validate():
            current_user.modify(username=update_username_form.username.data)
            current_user.save()
            return redirect(url_for('users.account'))

        if update_profile_pic_form.submit_picture.data and update_profile_pic_form.validate():
            img = update_profile_pic_form.picture.data
            filename = secure_filename(img.filename)
            content_type = f'images/{filename[-3:]}'

            if current_user.profile_pic.get() is None:
                current_user.profile_pic.put(img.stream, content_type=content_type)
            else:
                current_user.profile_pic.replace(img.stream, content_type=content_type)
            
            current_user.save()
            return redirect(url_for('users.account'))
        
    bytes_im = BytesIO(current_user.profile_pic.read())
    image = base64.b64encode(bytes_im.getvalue()).decode() if bytes_im else None
    
    return render_template('account.html', 
                           image=image, 
                           update_username_form=update_username_form, 
                           update_profile_pic_form=update_profile_pic_form)