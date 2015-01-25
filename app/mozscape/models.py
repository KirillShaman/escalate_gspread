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
from app import flask_app, datetime, db
import re
from multiprocessing.pool import ThreadPool as Pool
import requests
import bs4
from peewee import *
from app.gspreadsheet import Gspreadsheet
from app import GUser, werkzeug_cache
from lsapi import lsapi

# ________________________________________________________________________

class Mozscape(Model):
  name = CharField()
  runnable = CharField()
  gspread_link = CharField()
  urls = CharField(null=True)
  created_at = DateTimeField(null=True)
  updated_at = DateTimeField(null=True)

  class Meta:
    database = db
    db_table = 'mozscapes'

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

class MozscapeResult(Model):
  name = CharField()
  url = CharField()
  # Title 1 ut : title of the page, if available:
  ut = CharField(null=True)
  # External Equity Links  32  ueid : number of external equity links to the URL:
  ueid = IntegerField(null=True)
  # Links 2048  uid : number of links (equity or nonequity or not, internal or external) to the URL:
  uid = IntegerField(null=True)
  # MozRank: URL  16384 umrp + umrr : normalized 10-point MozRank score of the URL:
  umrp = FloatField(null=True)
  umrr = FloatField(null=True)
  # MozRank: Subdomain  32768 fmrp + fmrr : MozRank of the URL's subdomain, in both the normalized 10-point score (fmrp) and the raw score (fmrr):
  fmrp = FloatField(null=True)
  fmrr = FloatField(null=True)
  # HTTP Status Code  536870912 us : HTTP status code recorded by Mozscape for this URL, if available:
  us = CharField(null=True)
  # Page Authority  34359738368 upa : normalized 100-point score representing the likelihood of the URL to rank well in search engine results:
  upa = FloatField(null=True)
  # Domain Authority 68719476736 pda : normalized 100-point score representing the likelihood of the domain of the URL to rank well in search engine results:
  pda = FloatField(null=True)
  # not available in lsapi.py:
  # Time last crawled 144115188075855872  ulc : time and date on which Mozscape last crawled the URL, returned in Unix epoch format:
  # ulc = CharField(null=True)
  timestamp = DateTimeField(null=True)

  # see: lsapi.py:
  # freeCols = (title |     title             = 1
  #   url |                 url               = 4
  #   externalLinks |       externalLinks     = 32
  #   links |               links             = 2048
  #   mozRank |             mozRank           = 16384
  #   subdomainMozRank |    subdomainMozRank  = 32768
  #   httpStatusCode |      httpStatusCode    = 536870912
  #   pageAuthority |       pageAuthority     = 34359738368
  #   domainAuthority)      domainAuthority   = 68719476736
  # example:
  # uid=342922
  # uu=moz.com/
  # ut=Moz: Inbound Marketing and SEO Software, Made Easy
  # us=200
  # upa=92.2836285362
  # ueid=107282
  # umrp=7.23380857979
  # fmrp=7.42225852475
  # umrr=2.66862560411e-07
  # fmrr=2.27434218654e-06
  # pda=93.1574960533

  class Meta:
    database = db
    db_table = 'mozscape_results'

  @staticmethod
  def moz_url_metrics(mozscape):
    results = []
    guser = werkzeug_cache.get('guser')
    gs = Gspreadsheet(guser.gmail, guser.gpassword, None)
    gs.login()
    ss = gs.gclient.open_by_url(mozscape.gspread_link)
    ws = ss.sheet1
    urls = gs.col_one(ws)
    # FIXME only use the first url at A2, for now
    url = urls[0]
    l = lsapi(flask_app.config['MOZSCAPE_API_ACCESS_ID'], flask_app.config['MOZSCAPE_API_SECRET_KEY'])
    try:
      # mozscape restriction is NOT to make parallel requests but batch them instead!!!
      now_timestamp = datetime.utcnow()
      nrow = 2
      metrics = l.urlMetrics(url)
      # gspread update cells in row:
      acells = ws.range("B%s:L%s" % (nrow, nrow))
      acells[0].value = metrics['uid']
      acells[1].value = metrics['uu']
      acells[2].value = metrics['ut']
      acells[3].value = metrics['us']
      acells[4].value = metrics['upa']
      acells[5].value = metrics['ueid']
      acells[6].value = metrics['umrp']
      acells[7].value = metrics['umrr']
      acells[8].value = metrics['fmrp']
      acells[9].value = metrics['fmrr']
      acells[10].value = metrics['pda']
      ws.update_cells(acells)

      mr = MozscapeResult.create(
          name=mozscape.name,
          url=url,
          uid=metrics['uid'],
          uu=metrics['uu'],
          ut=metrics['ut'],
          us=metrics['us'],
          upa=metrics['upa'],
          ueid=metrics['ueid'],
          umrp=metrics['umrp'],
          umrr=metrics['umrr'],
          fmrp=metrics['fmrp'],
          fmrr=metrics['fmrr'],
          pda=metrics['pda'],
          timestamp=now_timestamp
      )
    except Exception as e:
      print("Error: moz_url_metrics:\n%s" % e)
    return len(results)

  def get_id(self):
    try:
      return unicode(self.id) # python 2
    except NameError:
      return str(self.id) # python 3

  def __repr__(self):
    return 'id={}, name={}'.format(self.id, self.name)
