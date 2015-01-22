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

from __future__ import print_function
import os
import time
from datetime import datetime
from dateutil.parser import parse as parse_date
from flask import Flask
# from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask import flash, redirect, session, url_for, render_template
from flask import request, send_from_directory, g
import jinja2
from functools import wraps
from peewee import *
from app.gspreadsheet import Gspreadsheet
from werkzeug.contrib.cache import SimpleCache
from models import GUser

# it's a bit confusing referring to "controllers" as "views",
# well, when you are use to rails ... but when in Rome
#
# why "flask_app" instead of "app" ?
#   coz it's clearer as to what "app" is referring to, i.e. a folder called "app"
#   and "flask_app" is referring to "Flask(__name__)" ... IMHO
#
# why an "app" folder instead of "project" ?
#   coz it's more like rails ... what's in a name

flask_app = Flask(__name__)
# bcrypt = Bcrypt(flask_app)

# flask_app.config.from_object(os.environ['APP_SETTINGS']) # see config.py
# if not using virtualenvwrapper and "nano $VIRTUAL_ENV/bin/postactivate",
# do this instead of "flask_app.config.from_object(os.environ['APP_SETTINGS'])":
flask_app.config.from_object('config.ProductionConfig') # see config.py

db = SqliteDatabase(flask_app.config['DATABASE'])

# used to keep gmail/password in memory:
werkzeug_cache = SimpleCache()
# note: on any server restart or reload during testing the cache is 
#       automatically cleared and a user must re-login
#       ... annoying during testing, but a good thing

@flask_app.before_request
def before_request():
  # try:
  #   guser = werkzeug_cache.get('guser')
  #   print("before_request: cache: %s, %s, %s"%(guser.id,guser.gmail,guser.gpassword))
  # except:
  #   pass
  g.db = db
  g.db.connect()

@flask_app.after_request
def after_request(response):
  # try:
  #   guser = werkzeug_cache.get('guser')
  #   print("after_request: cache: %s, %s, %s"%(guser.id,guser.gmail,guser.gpassword))
  # except:
  #   pass
  g.db.close()
  return response

from app.home.views import home_blueprint
flask_app.register_blueprint(home_blueprint)

from app.counters.views import counters_blueprint
flask_app.register_blueprint(counters_blueprint)

from app.channels.views import channels_blueprint
flask_app.register_blueprint(channels_blueprint)

from app.crawlers.views import crawlers_blueprint
flask_app.register_blueprint(crawlers_blueprint)

from app.functions.views import functions_blueprint
flask_app.register_blueprint(functions_blueprint)

from app.users.views import users_blueprint
flask_app.register_blueprint(users_blueprint)

login_manager = LoginManager()
login_manager.init_app(flask_app)
login_manager.login_view = "users.login"
@login_manager.user_loader
def load_user(user_id):
  # user = User.find_by_id(user_id) # db based login
  guser = werkzeug_cache.get('guser')
  if guser is None:
    pass
  else:
    if user_id == guser.id:
      pass
    else:
      guser = None
  return guser

# the following is needed coz the app uses "bootstrap" glyphicons:
# note: in production using nginx/whatever you will want to do this another way!
@flask_app.route('/fonts/<path:filename>')
def send_font(filename):
  static_images = flask_app.static_folder + "/fonts"
  return send_from_directory(static_images, filename)

# the following is needed coz "jquery.dataTables.min.css" refers to images like: "/images/sort_asc.png":
# note: in production using nginx/whatever you will want to do this another way!
@flask_app.route('/images/<path:filename>')
def send_image(filename):
  static_images = flask_app.static_folder + "/images"
  return send_from_directory(static_images, filename)

# why not handle 400, 404, and 500 errors here ?
#   coz this app is more of a private "tool",
#   and not a public facing internet app ...

# FIXME add some logging, in case users encounter bugs
