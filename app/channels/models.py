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

class ChannelCounter(Model):
  name = CharField()
  runnable = CharField()
  gspread_link = CharField()
  channel = CharField(null=True)
  created_at = DateTimeField(null=True)
  updated_at = DateTimeField(null=True)

  class Meta:
    database = db
    db_table = 'channel_counters'

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

class Channel(Model):
  ROOT_URL_PREFIX  = 'http://www.youtube.com/user/'
  ROOT_URL_SUFFIX  = '/videos'

  name = CharField()
  channel = CharField()
  url = CharField()
  title = CharField(null=True)
  views = IntegerField(null=True)
  likes = IntegerField(null=True)
  dislikes = IntegerField(null=True)
  timestamp = DateTimeField(null=True)

  class Meta:
    database = db
    db_table = 'channel_counts'

  def get_id(self):
    try:
      return unicode(self.id) # python 2
    except NameError:
      return str(self.id) # python 3

  def __repr__(self):
    return 'id={}, name={}, url={}, title={}'.format(self.id, self.name, self.url, self.title)

  @classmethod
  def get_video_page_urls(cls, channel):
    response = requests.get(Channel.ROOT_URL_PREFIX + channel + Channel.ROOT_URL_SUFFIX)
    soup = bs4.BeautifulSoup(response.text)
    urls = []
    for title in soup.findAll('h3', attrs={'class': 'yt-lockup-title'}):
      urls.append("https://www.youtube.com%s" % title.find('a')['href'])
    return urls

  @classmethod
  def get_video_data(cls, video_page_url):
    video_data = {}
    video_data['url'] = video_page_url
    video_data['title'] = ""
    video_data['views'] = 0
    video_data['likes'] = 0
    video_data['dislikes'] = 0
    try:
      response = requests.get(
        video_data['url'],
        headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36'}
      )
      soup = bs4.BeautifulSoup(response.text)
      video_data['title'] = soup.select('span.watch-title')[0].get_text().strip()
      video_data['views'] = int(re.sub('[^0-9]', '', soup.select('.watch-view-count')[0].get_text().split()[0]))
      video_data['likes'] = int(re.sub('[^0-9]', '',
        soup.select('#watch-like-dislike-buttons span.yt-uix-button-content')[0].get_text().split()[0]))
      video_data['dislikes'] = int(re.sub('[^0-9]', '',
        soup.select('#watch-like-dislike-buttons span.yt-uix-button-content')[2].get_text().split()[0]))
    except Exception as e:
      # some or all of the channels could not be scraped
      print("Error: Channel:get_video_data: %s"%e)
      pass
    return video_data

  @staticmethod
  def scrape(video_counter):
    guser = werkzeug_cache.get('guser')
    gs = Gspreadsheet(guser.gmail, guser.gpassword, None)
    gs.login()
    ss = gs.gclient.open_by_url(video_counter.gspread_link)
    ws = ss.sheet1
    urls = gs.col_one(ws)
    results = []
    try:
      pool = Pool(flask_app.config['MULTIPROCESSING_POOL_SIZE'])
      # video_page_urls = Channel.get_video_page_urls(channel)
      # results = pool.map(Channel.get_video_data, video_page_urls)
      results = pool.map(Channel.get_video_data, urls)
      now_timestamp = datetime.utcnow()
      nrow = 2
      for i in range(len(results)):
        # gspread update cells in row:
        acells = ws.range("B%s:E%s" % (nrow, nrow))
        acells[0].value = results[i]['title']
        acells[1].value = results[i]['views']
        acells[2].value = results[i]['likes']
        acells[3].value = results[i]['dislikes']
        ws.update_cells(acells)
        c = Channel.create(
          name=video_counter.name,
          channel='',
          url=results[i]['url'],
          title=results[i]['title'], 
          views=results[i]['views'],
          likes=results[i]['likes'],
          dislikes=results[i]['dislikes'],
          timestamp=now_timestamp
        )
        nrow += 1
    except Exception as e:
      print("Error: Channel:channel_scrape:\n%s" % e)
    return len(results)
