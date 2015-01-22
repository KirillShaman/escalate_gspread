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

# ________________________________________________________________________

class SocialCounter(Model):
  name = CharField()
  runnable = CharField()
  gspread_link = CharField()
  urls = CharField(null=True)
  created_at = DateTimeField(null=True)
  updated_at = DateTimeField(null=True)

  class Meta:
    database = db
    db_table = 'social_counters'

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

class SocialCount(Model):
  name = CharField()
  url = CharField()
  tweets = IntegerField(null=True)
  google_plusses = IntegerField(null=True)
  fb_total = IntegerField(null=True)
  fb_shares = IntegerField(null=True)
  fb_likes = IntegerField(null=True)
  fb_comments = IntegerField(null=True)
  fb_clicks = IntegerField(null=True)
  timestamp = DateTimeField(null=True)

  class Meta:
    database = db
    db_table = 'social_counts'

  @staticmethod
  def fetch_counters(social_counter):
    guser = werkzeug_cache.get('guser')
    gs = Gspreadsheet(guser.gmail, guser.gpassword, None)
    gs.login()
    ss = gs.gclient.open_by_url(social_counter.gspread_link)
    ws = ss.sheet1
    urls = gs.col_one(ws)
    results = []
    try:
      pool = Pool(flask_app.config['MULTIPROCESSING_POOL_SIZE'])
      results = pool.map(SocialCount.get_url_data, urls)
      now_timestamp = datetime.utcnow()
      nrow = 2
      for i in range(len(results)):
        # gspread update cells in row:
        acells = ws.range("B%s:H%s" % (nrow, nrow))
        acells[0].value = results[i]['tweets']
        acells[1].value = results[i]['plusses']
        acells[2].value = results[i]['total_count']
        acells[3].value = results[i]['share_count']
        acells[4].value = results[i]['like_count']
        acells[5].value = results[i]['comment_count']
        acells[6].value = results[i]['click_count']
        ws.update_cells(acells)
        c = SocialCount.create(
            name=social_counter.name,
            url=results[i]['url'],
            tweets=results[i]['tweets'],
            google_plusses=results[i]['plusses'],
            fb_total=results[i]['total_count'],
            fb_shares=results[i]['share_count'],
            fb_likes=results[i]['like_count'],
            fb_comments=results[i]['comment_count'],
            fb_clicks=results[i]['click_count'],
            timestamp=now_timestamp
        )
        nrow += 1
    except Exception as e:
      print("Error: fetch_counters:\n%s" % e)
    return len(results)

  def get_id(self):
    try:
      return unicode(self.id) # python 2
    except NameError:
      return str(self.id) # python 3

  def __repr__(self):
    return 'id={}, title={}'.format(self.id, self.title)

  @classmethod
  def get_urls(cls, urls):
    return urls.split("\n")

  @classmethod
  def get_url_data(cls, url):
    url_data = {}
    url_data['url'] = url
    url_data['total_count'] = 0
    url_data['share_count'] = 0
    url_data['like_count'] = 0
    url_data['comment_count'] = 0
    url_data['click_count'] = 0
    url_data['tweets'] = 0
    url_data['plusses'] = 0
    try:
      # do 3 requests (plusses, tweets, fbshares) to get all counts for each url:
      # facebook counts:
      api = "https://graph.facebook.com/fql?q=SELECT%20like_count,%20total_count,%20share_count,%20click_count,%20comment_count%20FROM%20link_stat%20WHERE%20url%20=%20%27"
      respobj = requests.get(api + url + "%27")
      respobj.raise_for_status() # do this coz responses other than 200 are not considered exceptions
      adict = respobj.json()
      url_data['total_count']   = adict['data'][0]['total_count']
      url_data['share_count']   = adict['data'][0]['share_count']
      url_data['like_count']    = adict['data'][0]['like_count']
      url_data['comment_count'] = adict['data'][0]['comment_count']
      url_data['click_count']   = adict['data'][0]['click_count']
      # tweets:
      api = "http://urls.api.twitter.com/1/urls/count.json?url="
      respobj = requests.get(api + url)
      respobj.raise_for_status() # do this coz responses other than 200 are not considered exceptions
      adict = respobj.json()
      url_data['tweets'] = adict["count"]
      # plusses:
      api = "https://clients6.google.com/rpc"
      jobj = '''{
        "method":"pos.plusones.get",
        "id":"p",
        "params":{
            "nolog":true,
            "id":"%s",
            "source":"widget",
            "userId":"@viewer",
            "groupId":"@self"
            },
        "jsonrpc":"2.0",
        "key":"p",
        "apiVersion":"v1"
      }''' % (url)
      respobj = requests.post(api, jobj)
      respobj.raise_for_status() # do this coz responses other than 200 are not considered exceptions
      adict = respobj.json()
      url_data['plusses'] = int(adict['result']['metadata']['globalCounts']['count'])
    except requests.exceptions.RequestException as e:
      print("requests.exceptions.RequestException Error=%s"%e)
      pass
    except KeyError as e:
      # need a logger instead of: print("Error:\n%s"%e)
      print("Error: KeyError: %s"%e)
      pass
    except Exception as e:
      # some or all of the counters could not be scraped
      print("Error: %s"%e)
      pass
    return url_data
