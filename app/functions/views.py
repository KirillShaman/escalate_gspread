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
from app import flask_app, time, datetime, parse_date, db
from flask import flash, redirect, session, Response, url_for, render_template, Blueprint, request, send_from_directory
from flask.ext.login import login_required
from flask.ext.login import current_user
# from jinja2 import Environment
import jinja2
from app.functions.models import UserFunction, FunctionResult
from forms import UserFunctionForm
from user_defined_functions import UserDefinedFunctions
import pickle

functions_blueprint = Blueprint('functions', __name__, template_folder='templates')

errors = []

list_user_funcs = dir(UserDefinedFunctions)
# pluck out the "user_" functions:
user_funcs = [uf for uf in list_user_funcs if "user_" in uf]

def get_user_functions():
  app_root = os.path.dirname(os.path.abspath(__file__))
  ufpath = os.path.join(app_root, 'user_defined_functions.py')
  uf = open(ufpath)
  return uf.read()

def basename(value):
  return os.path.basename(value)
jinja2.filters.FILTERS['basename'] = basename

def format_number(value):
  return "{:,}".format(value)
jinja2.filters.FILTERS['format_number'] = format_number

def datetimeformat(value, format='%a %Y/%m/%d %T'):
  return parse_date(value).strftime(format)
jinja2.filters.FILTERS['datetimeformat'] = datetimeformat

def array_to_string(value):
  return ', '.join(value)
jinja2.filters.FILTERS['array_to_string'] = array_to_string

def array_len(value):
  return len(value)
jinja2.filters.FILTERS['array_len'] = array_len

def what_type(value):
  return type(value)
jinja2.filters.FILTERS['what_type'] = what_type

def unpickle(value):
  return pickle.loads(value)
jinja2.filters.FILTERS['unpickle'] = unpickle

@functions_blueprint.route('/run_function')
@login_required
def run_function():
  id = request.args.get('id', None)
  if id is None:
    flash('Error: user function id is missing!')
    return redirect(url_for('functions.functions_list'))
  func = UserFunction.get(UserFunction.id==id)
  if func.is_runnable():
    results = FunctionResult.perform_function(func)
  else:
    results = {}
  flash("Ran user function: %s" % func.name)
  return redirect(url_for('functions.functions_list'))

@functions_blueprint.route('/functions_summary')
@login_required
def functions_summary():
  view_errors = request.args.get('e', None)
  id = request.args.get('id', None)
  if id is None:
    flash('Error: id is missing for User function summary page!')
    return redirect(url_for('counters.functions_list'))
  uf = UserFunction.get(UserFunction.id==id)
  if view_errors is None:
    func_results = FunctionResult.select().where(
      (FunctionResult.name == uf.name) & (FunctionResult.tag == 'k')
    ).order_by(FunctionResult.timestamp.desc())
  else:
    func_results = FunctionResult.select().where(
      (FunctionResult.name == uf.name) & (FunctionResult.tag == 'e')
    ).order_by(FunctionResult.timestamp.desc())
  first_row = None
  # loop once to set "first_row" so the page can create the dynamic column headers:
  for fr in func_results:
    first_row = fr
    break
  return render_template('functions_summary.html', current_user=current_user,
    func_results=func_results, func=uf, id=id, first_row=first_row
  )

@functions_blueprint.route('/functions_new')
@login_required
def functions_new():
  form = UserFunctionForm()
  ufs = get_user_functions()
  return render_template('function.html', current_user=current_user, ufs=ufs, user_funcs=user_funcs, form=form, new_function=True)

@functions_blueprint.route('/functions_create', methods=['POST'])
@login_required
def functions_create():
  form = UserFunctionForm(request.form)
  form.validate()
  # params = request.form.get('params')
  # params_stripped = "\n".join([ll.strip() for ll in params.splitlines() if ll.strip()])
  new_function = True
  if form.errors:
    pass
  else:
    now = datetime.utcnow()
    function = UserFunction.create(
      name=request.form.get('name'),
      runnable=request.form.get('runnable'),
      function=request.form.get('function'),
      gspread_link=request.form.get('gspread_link'),
      # params=params_stripped,
      params=None,
      created_at=now,
      updated_at=now
    )
    new_function = False
    form = UserFunctionForm(None, function)
    flash('User function was created')
    return redirect(url_for('functions.functions_list'))
  ufs = get_user_functions()
  return render_template('function.html', current_user=current_user, ufs=ufs, form=form, new_function=new_function)

@functions_blueprint.route('/functions_update', methods=['GET', 'POST'])
@login_required
def functions_update():
  # FIXME ugly code to do both edit/update
  if request.method == 'GET':
    id = request.args.get('id', '')
    func = UserFunction.get(UserFunction.id==id)
    form = UserFunctionForm(None, func)
  else:
    id = request.form.get('id')
    func = UserFunction.get(UserFunction.id==id)
    form = UserFunctionForm(request.form)
    form.validate()
    # params = request.form.get('params')
    # params_stripped = "\n".join([line.strip() for line in params.splitlines() if line.strip()])
    if form.errors:
      pass
    else:
      now = datetime.utcnow()
      func.name = request.form.get('name')
      func.runnable = request.form.get('runnable')
      func.function = request.form.get('function')
      func.gspread_link=request.form.get('gspread_link')
      # func.params = params_stripped
      func.params = None
      func.updated_at = now
      func.save()
      new_function = False
      form = UserFunctionForm(None, func)
      flash('User function was updated')
      return redirect(url_for('functions.functions_list'))
  ufs = get_user_functions()
  return render_template('function.html', current_user=current_user, ufs=ufs, form=form, new_function=False, id=id)

@functions_blueprint.route('/functions_list')
@login_required
def functions_list():
  funcs = UserFunction.select()
  return render_template('functions_list.html', current_user=current_user, funcs=funcs)
