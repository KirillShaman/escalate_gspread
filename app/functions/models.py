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
import re
import pickle
from multiprocessing.pool import ThreadPool as Pool
import requests
import bs4
from app import flask_app, datetime, db
from user_defined_functions import UserDefinedFunctions
from peewee import *
from app.gspreadsheet import Gspreadsheet
from app import GUser, werkzeug_cache

# ________________________________________________________________________

class UserFunction(Model):
  name = CharField()
  runnable = CharField()
  function = CharField()
  gspread_link = CharField()
  params = CharField(null=True)
  created_at = DateTimeField(null=True)
  updated_at = DateTimeField(null=True)

  class Meta:
    database = db
    db_table = 'user_functions'

  def get_id(self):
    try:
      return unicode(self.id) # python 2
    except NameError:
      return str(self.id) # python 3

  def is_runnable(self):
    return self.runnable == 'yes'

  def __repr__(self):
    return 'id={}, name={}'.format(self.id, self.name)

# ________________________________________________________________________

class FunctionResult(Model):
  tag = CharField()
  name = CharField()
  function = CharField()
  params = CharField(null=True)
  results = BlobField(null=True)
  timestamp = DateTimeField(null=True)

  class Meta:
    database = db
    db_table = 'function_results'

  @staticmethod
  def perform_function(func):
    now_timestamp = datetime.utcnow()
    results = {}
    name = func.name
    function = func.function.split('(')
    guser = werkzeug_cache.get('guser')
    gs = Gspreadsheet(guser.gmail, guser.gpassword, None)
    gs.login()
    ss = gs.gclient.open_by_url(func.gspread_link)
    ws = ss.sheet1
    params = gs.col_one(ws)
    run_count = 1
    for fp in params:
      result = {}
      args = fp.split(', ')
      result['function'] = function[0]
      result['params'] = args
      try:
        # test error handling:
        # if fp == 'italian greyhound':
        #   raise Exception(fp)
        func_result = getattr(UserDefinedFunctions, function[0])(*args)
        result['result'] = func_result
      except Exception as e:
        aresult = "Exception: %s" % e
        result['result'] = [{'error' : aresult}]
        print("Error: running user function: %s\n\tException: %s" % (function[0], e))
        pass
      results[run_count] = result
      run_count += 1
    nrow = 2
    for key, func_result in results.items():
      try:
        is_error = 'error' in func_result['result'][0]
        # gspread update cells in row:
        acells = ws.range("B%s:F%s" % (nrow, nrow))
        acell = 0
        for fr in func_result['result']:
          if is_error:
            acells[acell].value = fr.get('error', '')
          else:
            acells[acell].value = fr.get('data', '')
          acell += 1
        ws.update_cells(acells)
        func_res = FunctionResult.create(
          tag='e' if is_error else 'k',
          name=name,
          function=func_result['function'],
          params=','.join(func_result['params']),
          results=pickle.dumps(func_result['result']),
          timestamp=now_timestamp
        )
        nrow += 1
      except Exception as e:
        print("Error: perform_function:\n%s" % e)
    return results

  def get_id(self):
    try:
      return unicode(self.id) # python 2
    except NameError:
      return str(self.id) # python 3

  def __repr__(self):
    return 'id={} tag={}, name={}'.format(self.id, self.tag, self.name)
