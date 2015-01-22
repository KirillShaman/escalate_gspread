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
from app import flask_app, time, datetime, parse_date, db, werkzeug_cache
from flask import flash, redirect, session, Response, url_for, render_template, Blueprint, request, send_from_directory
from flask.ext.login import login_required
from flask.ext.login import current_user
# from jinja2 import Environment
import jinja2
from app.counters.models import SocialCounter, SocialCount
from forms import SocialCounterForm
import requests
import StringIO
from playhouse.csv_loader import *

counters_blueprint = Blueprint('counters', __name__, template_folder='templates')

errors = []

def basename(value):
  return os.path.basename(value)
jinja2.filters.FILTERS['basename'] = basename

def format_number(value):
  return "{:,}".format(value)
jinja2.filters.FILTERS['format_number'] = format_number

def datetimeformat(value, format='%a %Y/%m/%d %T'):
  return parse_date(value).strftime(format)
jinja2.filters.FILTERS['datetimeformat'] = datetimeformat

@counters_blueprint.route('/count_now')
@login_required
def count_now():
  # gspread columns, does the name matter? no, just the proper number of columns for the results:
  # url, tweets, google_plusses, fb_total, fb_shares, fb_likes, fb_comments, fb_clicks
  id = request.args.get('id', None)
  if id is None:
    flash('Error: id is missing, but is required to run a Social counter!')
    return redirect(url_for('counters.counters_list'))
  sc = SocialCounter.get(SocialCounter.id==id)
  if sc.is_runnable():
    # processed = SocialCount.fetch_counters(sc.name, sc.urls)
    processed = SocialCount.fetch_counters(sc)
  flash("Social counts updated for: '%s'" % sc.name)
  return redirect(url_for('counters.counters_list'))

@counters_blueprint.route('/counters_summary')
@login_required
def counters_summary():
  id = request.args.get('id', None)
  if id is None:
    flash('Error: id is missing for Social counter summary page!')
    return redirect(url_for('counters.counters_list'))
  sc = SocialCounter.get(SocialCounter.id==id)
  counters = SocialCount.select().where(SocialCount.name==sc.name).order_by(SocialCount.timestamp.desc())
  return render_template('counters_summary.html', current_user=current_user, counters=counters, id=id)

# @counters_blueprint.route('/counters_to_ethercalc')
# # @login_required
# def counters_to_ethercalc():
#   id = request.args.get('id', None)
#   if id is None:
#     flash('Error: id is missing for Social counter summary page!')
#     return redirect(url_for('counters.counters_list'))
#   sc = SocialCounter.get(SocialCounter.id==id)
#   counters = SocialCount.select(
#     SocialCount.name, SocialCount.tweets, SocialCount.google_plusses,
#       SocialCount.fb_total, SocialCount.fb_shares, SocialCount.fb_likes, SocialCount.fb_comments, SocialCount.fb_clicks
#     ).where(SocialCount.name==sc.name).order_by(SocialCount.timestamp.desc())
#   sio = StringIO.StringIO() # so we have a "file-like" object
#   csv_counters = dump_csv(counters, sio, close_file=False)
#   url = "%s/_" % flask_app.config['ETHERCALC_URL']
#   response = requests.post(url, data=csv_counters.getvalue())
#   spreadsheet_name = response.text
#   url = "%s%s" % (flask_app.config['ETHERCALC_URL'], spreadsheet_name)
#   csv_counters.close()
#   return redirect(url)

@counters_blueprint.route('/counters_new')
@login_required
def counters_new():
  form = SocialCounterForm()
  return render_template('counter.html', current_user=current_user, form=form, new_counter=True)

@counters_blueprint.route('/counters_create', methods=['POST'])
@login_required
def counters_create():
  form = SocialCounterForm(request.form)
  form.validate()
  # urls = request.form.get('urls')
  # urls_stripped = "\n".join([ll.rstrip() for ll in urls.splitlines() if ll.strip()])
  new_counter = True
  if form.errors:
    pass
  else:
    now = datetime.datetime.utcnow()
    counter = SocialCounter.create(
      name=request.form.get('name'),
      runnable=request.form.get('runnable'),
      gspread_link=request.form.get('gspread_link'),
      # urls=urls_stripped,
      urls=None, # or obtained from gspread?
      created_at=now,
      updated_at=now
    )
    new_counter = False
    form = SocialCounterForm(None, counter)
    flash('Social counter was created')
    return redirect(url_for('counters.counters_list'))
  return render_template('counter.html', current_user=current_user, form=form, new_counter=new_counter)

@counters_blueprint.route('/counters_update', methods=['GET', 'POST'])
@login_required
def counters_update():
  if request.method == 'GET':
    id = request.args.get('id', '')
    counter = SocialCounter.get(SocialCounter.id==id)
    form = SocialCounterForm(None, counter)
  else:
    id = request.form.get('id')
    counter = SocialCounter.get(SocialCounter.id==id)
    form = SocialCounterForm(request.form)
    form.validate()
    # urls = request.form.get('urls')
    # urls_stripped = "\n".join([line.rstrip() for line in urls.splitlines() if line.strip()])
    if form.errors:
      pass
    else:
      now = datetime.datetime.utcnow()
      counter.name = request.form.get('name')
      counter.runnable = request.form.get('runnable')
      counter.gspread_link = request.form.get('gspread_link')
      # counter.urls = urls_stripped
      counter.urls = None # or obtained from gspread?
      counter.updated_at = now
      counter.save()
      new_counter = False
      form = SocialCounterForm(None, counter)
      flash('Social counter was updated')
      return redirect(url_for('counters.counters_list'))
  return render_template('counter.html', current_user=current_user, form=form, new_counter=False, id=id)

@counters_blueprint.route('/counters_list')
@login_required
def counters_list():
  counters = SocialCounter.select()
  return render_template('counters_list.html', current_user=current_user, counters=counters)
