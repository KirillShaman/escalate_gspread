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

import os
from flask.ext.script import Manager
# if using login/logout do:
# from app import bcrypt
from app import flask_app, datetime, db
from app.users.models import User
from app.counters.models import SocialCounter, SocialCount
from app.channels.models import ChannelCounter, Channel
from app.crawlers.models import Crawler, CrawlerPage
from app.mozscape.models import Mozscape, MozscapeResult, MozscapeIndexMetadata
from app.functions.models import UserFunction, FunctionResult
from apscheduler.schedulers.blocking import BlockingScheduler
from jobs import *
from waitress import serve

# flask_app.config.from_object(os.environ['APP_SETTINGS'])
# if not using virtualenvwrapper and "nano $VIRTUAL_ENV/bin/postactivate",
# do this instead of "flask_app.config.from_object(os.environ['APP_SETTINGS'])":
flask_app.config.from_object('config.ProductionConfig')

manager = Manager(flask_app)

# usage: python manage.py jobs
@manager.command
def jobs():
  """
    Run background job scheduler.
    This is just a simple scheduler with no persistence,
    and run as a separate process from the flask app.
  """
  scheduler = BlockingScheduler()

  # *************
  # schedule jobs:
  # *************
  scheduler.add_job(social_counters, 'cron', day_of_week='*', hour=2) # 2am
  scheduler.add_job(youtube_channels, 'cron', day_of_week='*', hour=3) # 3am
  scheduler.add_job(crawlers, 'cron', day_of_week='*', hour=4) # 4am
  # *************

  print('Job scheduler started at: %s'%datetime.utcnow())
  scheduler.start()

# usage:
#   python manage.py db_create
#   python manage.py seeds
# @manager.command
# def seeds():
#   """Seed initial admin user."""
#   db.connect()
#   password_digest = bcrypt.generate_password_hash("seo")
#   now = datetime.utcnow()
#   try:
#     admin = User.query.filter_by(username='seo').first()
#   except Exception as e:
#     admin = None
#   if admin is None:
#     db.session.add(User("seo", "seo@changeme.com", password_digest))
#     db.session.commit()
#     print("Seeds: created the initial admin user: seo+seo")
#   else:
#     # how to update:
#     # admin.email = "seo@changeme.com"
#     # db.session.commit()
#     print("Seeds: found the admin user: '%s', so no seed required" % admin.username)
#   db.close()

# usage:
#   python manage.py db_create
@manager.command
def db_create():
  db.connect()
  User.create_table(True) # True means fail siliently if table exists
  SocialCounter.create_table(True)
  SocialCount.create_table(True)
  ChannelCounter.create_table(True)
  Channel.create_table(True)
  UserFunction.create_table(True)
  FunctionResult.create_table(True)
  Crawler.create_table(True)
  CrawlerPage.create_table(True)
  Mozscape.create_table(True)
  MozscapeResult.create_table(True)
  MozscapeIndexMetadata.create_table(True)
  db.close()

# usage:
#   python manage.py waitress_please
@manager.command
def waitress_please():
  serve(flask_app, port=5000) # use waitress

if __name__ == '__main__':
  manager.run()
