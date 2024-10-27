from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_required, login_user, logout_user
import base64
from io import BytesIO
from .. import bcrypt
from werkzeug.utils import secure_filename
from ..forms import RegistrationForm, LoginForm, UpdateUsernameForm, UpdateProfilePicForm, ReferFriendForm
from ..models import User
from propelauth_flask import init_auth

api_key = "e878a5b9d5426138e344d22c10701edc195b8b2cd8586fb5cfb536c327258249747d01a567413e096999ab8589629152"
auth_url = "https://382477484.propelauthtest.com"
auth = init_auth(auth_url, api_key)


users = Blueprint("users", __name__)

""" ************ User Management views ************ """


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('species.index'))
    
    registration_form = RegistrationForm()
    
    if registration_form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(registration_form.password.data).decode('utf-8')
        new_user = User(username=registration_form.username.data, 
                        email=registration_form.email.data,
                        password=hashed_password)
        new_user.save()
        return redirect(url_for('users.login'))

    return render_template('register.html', registration_form=registration_form)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('species.index'))
    
    login_form = LoginForm()

    if login_form.validate_on_submit():
        user = User.objects(username=login_form.username.data).first()

        if (user is not None) and (bcrypt.check_password_hash(user.password, login_form.password.data)):
            login_user(user)
            return redirect(url_for('users.account'))
        else:
            flash('Incorrect username or password. Please try again.')
    
    return render_template('login.html', login_form=login_form)


@users.route("/logout")
@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()

        return redirect(url_for('species.index'))


# @users.route("/account", methods=["GET", "POST"])
# @login_required
# def account():
    
#     update_username_form = UpdateUsernameForm()
#     update_profile_pic_form = UpdateProfilePicForm()
#     image = None
#     if request.method == "POST":
#         if update_username_form.submit_username.data and update_username_form.validate():
#             current_user.modify(username=update_username_form.username.data)
#             current_user.save()
#             return redirect(url_for('users.account'))

#         if update_profile_pic_form.submit_picture.data and update_profile_pic_form.validate():
#             img = update_profile_pic_form.picture.data
#             filename = secure_filename(img.filename)
#             content_type = f'images/{filename[-3:]}'

#             if current_user.profile_pic.get() is None:
#                 current_user.profile_pic.put(img.stream, content_type=content_type)
#             else:
#                 current_user.profile_pic.replace(img.stream, content_type=content_type)
            
#             current_user.save()
#             return redirect(url_for('users.account'))
        
#     bytes_im = BytesIO(current_user.profile_pic.read())
#     image = base64.b64encode(bytes_im.getvalue()).decode() if bytes_im else None
    
#     return render_template('account.html', 
#                            image=image, 
#                            update_username_form=update_username_form, 
#                            update_profile_pic_form=update_profile_pic_form)


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
   update_username_form = UpdateUsernameForm()
   update_profile_pic_form = UpdateProfilePicForm()
   refer_friend_form = ReferFriendForm()
   if request.method == "POST":
       if update_username_form.submit_username.data and update_username_form.validate():
           new_username = update_username_form.username.data
           current_user.modify(username=new_username)
           current_user.save()
           return redirect(url_for('species.user_detail', username=current_user.username, image=current_user.profile_pic))
       if update_profile_pic_form.submit_picture.data and update_profile_pic_form.validate():
           # TODO: handle update profile pic form submit
           new_picture = update_profile_pic_form.picture.data
           filename = secure_filename(new_picture.filename)
           content_type = f'images/{filename[-3:]}'
           if current_user.profile_pic.get() is None:
               current_user.profile_pic.put(new_picture.stream, content_type=content_type)
           else:
           # user has a profile picture => replace it
               current_user.profile_pic.replace(new_picture.stream, content_type=content_type)
           current_user.save()
           return redirect(url_for('species.user_detail', username=current_user.username, image=current_user.profile_pic))
       if refer_friend_form.submit_referral.data and refer_friend_form.validate():
           friend_email = refer_friend_form.friend_email.data
           redirect_to_url = url_for('species.user_detail', username=current_user.username, image=current_user.profile_pic, _external=True) # Customize your redirect URL
           # Create a magic link for the friend
           magic_link = auth.create_magic_link(
               email=friend_email,
               redirect_to_url=redirect_to_url,
               expires_in_hours=1,
               create_new_user_if_one_doesnt_exist=True,
           )
           #return redirect(url_for('users.account'))
           return render_template('account.html', update_username_form=update_username_form, update_profile_pic_form=update_profile_pic_form, refer_friend_form=refer_friend_form, magic_link = magic_link['url'])
   # TODO: handle get requests
   return render_template('account.html', update_username_form=update_username_form, update_profile_pic_form=update_profile_pic_form, refer_friend_form=refer_friend_form)