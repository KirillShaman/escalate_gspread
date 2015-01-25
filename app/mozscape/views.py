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
from app.mozscape.models import Mozscape, MozscapeResult
from forms import MozscapeForm
import requests
import StringIO
from playhouse.csv_loader import *

mozscape_blueprint = Blueprint('mozscape', __name__, template_folder='templates')

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

@mozscape_blueprint.route('/moz_now')
@login_required
def moz_now():
  id = request.args.get('id', None)
  if id is None:
    flash('Error: id is missing, but is required to get Mozscape data!')
    return redirect(url_for('mozscape.mozscapes_list'))
  moz = Mozscape.get(Mozscape.id==id)
  if moz.is_runnable():
    processed = MozscapeResult.moz_url_metrics(moz)
  flash("Mozscape data was updated for: '%s'" % moz.name)
  return redirect(url_for('mozscape.mozscapes_list'))

@mozscape_blueprint.route('/mozscapes_summary')
@login_required
def mozscapes_summary():
  id = request.args.get('id', None)
  if id is None:
    flash('Error: id is missing, but is required to get Mozscape data!')
    return redirect(url_for('mozscape.mozscapes_list'))
  moz = Mozscape.get(Mozscape.id==id)
  moz_results = MozscapeResult.select().where(MozscapeResult.name==moz.name).order_by(MozscapeResult.timestamp.desc())
  return render_template('mozscapes_summary.html', current_user=current_user, moz_results=moz_results, id=id)

@mozscape_blueprint.route('/mozscapes_new')
@login_required
def mozscapes_new():
  form = MozscapeForm()
  return render_template('mozscape.html', current_user=current_user, form=form, new_moz=True)

@mozscape_blueprint.route('/mozscapes_create', methods=['POST'])
@login_required
def mozscapes_create():
  form = MozscapeForm(request.form)
  form.validate()
  # urls = request.form.get('urls')
  # urls_stripped = "\n".join([ll.rstrip() for ll in urls.splitlines() if ll.strip()])
  new_moz = True
  if form.errors:
    pass
  else:
    now = datetime.datetime.utcnow()
    moz = Mozscape.create(
      name=request.form.get('name'),
      runnable=request.form.get('runnable'),
      gspread_link=request.form.get('gspread_link'),
      # urls=urls_stripped,
      urls=None, # obtained from gspread?
      created_at=now,
      updated_at=now
    )
    new_moz = False
    form = MozscapeForm(None, moz)
    flash('Mozscape was created')
    return redirect(url_for('mozscape.mozscapes_list'))
  return render_template('mozscape.html', current_user=current_user, form=form, new_moz=new_moz)

@mozscape_blueprint.route('/mozscapes_update', methods=['GET', 'POST'])
@login_required
def mozscapes_update():
  if request.method == 'GET':
    id = request.args.get('id', '')
    mozscape = Mozscape.get(Mozscape.id==id)
    form = MozscapeForm(None, mozscape)
  else:
    id = request.form.get('id')
    mozscape = Mozscape.get(Mozscape.id==id)
    form = MozscapeForm(request.form)
    form.validate()
    # urls = request.form.get('urls')
    # urls_stripped = "\n".join([line.rstrip() for line in urls.splitlines() if line.strip()])
    if form.errors:
      pass
    else:
      now = datetime.datetime.utcnow()
      mozscape.name = request.form.get('name')
      mozscape.runnable = request.form.get('runnable')
      mozscape.gspread_link = request.form.get('gspread_link')
      # mozscape.urls = urls_stripped
      mozscape.urls = None # or obtained from gspread?
      mozscape.updated_at = now
      mozscape.save()
      new_moz = False
      form = MozscapeForm(None, mozscape)
      flash('Mozscape was updated')
      return redirect(url_for('mozscape.mozscapes_list'))
  return render_template('mozscape.html', current_user=current_user, form=form, new_moz=False, id=id)

@mozscape_blueprint.route('/mozscapes_list')
@login_required
def mozscapes_list():
  mozs = Mozscape.select()
  return render_template('mozscapes_list.html', current_user=current_user, mozs=mozs)
