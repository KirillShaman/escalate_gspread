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
from app import flask_app, time, datetime, parse_date
from flask import flash, redirect, session, Response, url_for, render_template, Blueprint, request, send_from_directory
from flask.ext.login import login_required
from flask.ext.login import current_user
# from jinja2 import Environment
import jinja2
import gspread
from app.gspreadsheet import Gspreadsheet
from app import GUser, werkzeug_cache

ATOM_NS = 'http://www.w3.org/2005/Atom'
SPREADSHEET_NS = 'http://schemas.google.com/spreadsheets/2006'
BATCH_NS = 'http://schemas.google.com/gdata/batch'

def _ns(name):
    return '{%s}%s' % (ATOM_NS, name)

def _ns1(name):
    return '{%s}%s' % (SPREADSHEET_NS, name)

home_blueprint = Blueprint('home', __name__, template_folder='templates')

errors = []

def basename(value):
  return os.path.basename(value)
jinja2.filters.FILTERS['basename'] = basename

def format_number(value):
  return "{:,}".format(value)
jinja2.filters.FILTERS['format_number'] = format_number

def datetimeformat(value, format='%d/%m/%Y %H:%M:%S'):
  return parse_date(value).strftime(format)
jinja2.filters.FILTERS['datetimeformat'] = datetimeformat

@home_blueprint.route('/')
@login_required
def home():
  ip = request.remote_addr
  all_title = 'error: unable to retrieve google spreadsheet titles!'
  spreadsheet_titles = []
  guser = werkzeug_cache.get('guser')
  gs = Gspreadsheet(guser.gmail, guser.gpassword, None)
  gs_client = gs.login()
  if gs_client is None:
    pass
  else:
    all = gs.gclient.get_spreadsheets_feed()
    all_title = all.find(_ns('title')).text.lower().replace("available","",1).replace("-","for",1)
    for elem in all.findall(_ns('entry')):
      spreadsheet_titles.append(elem.find(_ns('title')).text)
  return render_template('home.html', current_user=current_user, ip=ip, all_title=all_title, spreadsheet_titles=spreadsheet_titles)
