# The MIT License (MIT)
# Escalate Copyright (c) [2014] [Chris Smith]

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from flask import flash, redirect, render_template, request, session, url_for, Blueprint
from flask.ext.login import login_user, login_required, logout_user
from flask.ext.login import current_user
from .forms import LoginForm
# from app.users.models import User, bcrypt
from app.users.models import User
from app.gspreadsheet import Gspreadsheet
from app import GUser, werkzeug_cache

users_blueprint = Blueprint('users', __name__, template_folder='templates')

# @users_blueprint.route('/login', methods=['GET', 'POST'])
# def login():
#   error = None
#   form = LoginForm(request.form)
#   if request.method == 'POST':
#     if form.validate_on_submit():
#       try:
#         user = User.find_by_username(request.form['username'])
#       except Exception as e:
#         print("Error: %s" % e)
#         user = None
#       if user is not None and bcrypt.check_password_hash(user.password_digest, request.form['password']):
#         login_user(user) # calls load_user, see: app/__init__.py
#         # flash('You were logged in.')
#         return redirect(url_for('home.home'))
#       else:
#         error = 'Invalid username or password.'
#   return render_template('login.html', form=form, error=error)

@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  form = LoginForm(request.form)
  if request.method == 'POST':
    if form.validate_on_submit():
      try:
        gs = Gspreadsheet(request.form['username'], request.form['password'], None)
        gs_client = gs.login()
        if gs_client is None:
          error = 'Invalid gmail or password.'
        else:
          werkzeug_cache.delete(1)
          guser = GUser(id=1, gmail=request.form['username'], gpassword=request.form['password'])
          werkzeug_cache.set('guser', guser, timeout=3 * 60 * 60) # lasts 3 hours
          login_user(guser) # calls load_user, see: app/__init__.py
          # flash('You were logged in!!!!!')
          return redirect(url_for('home.home'))
      except Exception as e:
        print("Error: %s" % e)
        error = 'Invalid gmail or password.'
  return render_template('login.html', form=form, error=error)

@users_blueprint.route('/logout')
@login_required
def logout():
  logout_user()
  # flash('You were logged out.')
  return redirect(url_for('users.login'))
