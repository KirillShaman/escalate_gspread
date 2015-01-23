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
import pickle
from page_analyzer import Page
from peewee import *
from app.gspreadsheet import Gspreadsheet
from app import GUser, werkzeug_cache

# ________________________________________________________________________

class Crawler(Model):
  name = CharField()
  runnable = CharField()
  crawl_status = CharField(null=True)
  gspread_link = CharField()
  url = CharField(null=True)
  crawled_at = DateTimeField(null=True)
  created_at = DateTimeField(null=True)
  updated_at = DateTimeField(null=True)

  class Meta:
    database = db
    db_table = 'crawlers'

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

class CrawlerPage(Model):
  name = CharField(null=True)
  url = CharField(null=True)
  sitemap = CharField(null=True)
  title_tag = CharField(null=True)
  meta_description = CharField(null=True)
  meta_keywords = CharField(null=True)
  warnings = CharField(null=True)
  h1_tag = CharField(null=True)
  a_tags = CharField(null=True)
  img_tags = CharField(null=True)
  plain_text = TextField(null=True)
  word_freqs = TextField(null=True)
  suggestions = TextField(null=True)
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
    db_table = 'crawled_pages'

  def get_id(self):
    try:
      return unicode(self.id) # python 2
    except NameError:
      return str(self.id) # python 3

  def __repr__(self):
    return 'id={}, name={}, url={}, sitemap={}, title_tag={}, warnings={}'.format(self.id, self.name, self.url, self.sitemap, self.title_tag, self.warnings)

  @staticmethod
  def suggestions(keywords):
    suggestions = []
    url = "http://google.com/complete/search?output=toolbar&q=%s" % keywords.replace(' ', '+')
    try:
      response = requests.get(url)
      soup = bs4.BeautifulSoup(response.text)
      results = soup.findAll("suggestion")
      for result in results:
        result_attrs = dict(result.attrs)
        suggestions.append(result_attrs)
    except Exception as e:
      print("Error:\n" % e)
    return suggestions

  @staticmethod
  def crawl(crawler):
    guser = werkzeug_cache.get('guser')
    gs = Gspreadsheet(guser.gmail, guser.gpassword, None)
    gs.login()
    ss = gs.gclient.open_by_url(crawler.gspread_link)
    ws = ss.sheet1
    urls = gs.col_one(ws)
    # only use the first url at A2, as it's probably
    # best to use a separate spreadsheet for each base url/site:
    url = urls[0]
    # url = 'http://104.236.92.144:8888/' # live demo restriction
    site = Page(url)
    pages = []
    try:
      now_timestamp = datetime.utcnow() # give all pages crawled the same timestamp
      # start with row 2 col B for output:
      nrow = 2
      for cp in site.crawl_and_analyze():
        # "crawl_and_analyze" is a generator that yields a Page object:
        pages.append(cp)
        # gspread update cells in row:
        acells = ws.range("B%s:Q%s" % (nrow, nrow))
        acells[0].value = cp.url
        acells[1].value = cp.title
        acells[2].value = cp.description
        acells[3].value = cp.keywords
        acells[4].value = ''
        for link in cp.links:
          acells[4].value += "%s\n" % link
        acells[5].value = "\n".join(cp.warnings)
        words = ""
        for word_count_tuple in cp.wordcount:
          words += "%s=%s\n" % (word_count_tuple[0], word_count_tuple[1])
        acells[6].value = words
        try:
          acells[7].value = ''
          suggested_keywords = CrawlerPage.suggestions( "%s %s" % (cp.wordcount[0][0], cp.wordcount[1][0]) )
          for suggested in suggested_keywords:
            for k,v in suggested.iteritems():
              acells[7].value += "%s\n" % v
        except:
          acells[7].value = ''
          pass
        acells[7].value = acells[7].value.rstrip()
        try:
          acells[8].value = ''
          suggested_keywords = CrawlerPage.suggestions( "%s %s %s" % (cp.wordcount[0][0], cp.wordcount[1][0], cp.wordcount[2][0]) )
          for suggested in suggested_keywords:
            for k,v in suggested.iteritems():
              acells[8].value += "%s\n" % v
        except:
          acells[8].value = ''
          pass
        acells[9].value = cp.twitter_count
        acells[10].value = cp.googleplusones
        acells[11].value = cp.fb_total_count
        acells[12].value = cp.fb_share_count
        acells[13].value = cp.fb_like_count
        acells[14].value = cp.fb_comment_count
        acells[15].value = cp.fb_click_count
        ws.update_cells(acells)
        crawler_page = CrawlerPage.create(
          name=crawler.name,
          url=cp.url,
          sitemap=None,
          title_tag=cp.title,
          meta_description=cp.description,
          meta_keywords=cp.keywords,
          warnings=','.join(cp.warnings),
          h1_tag=None,
          a_tags=cp.links,
          img_tags=None,
          plain_text=cp.page_text,
          word_freqs=pickle.dumps(cp.wordcount),
          tweets=cp.twitter_count,
          google_plusses=cp.googleplusones,
          fb_total=cp.fb_total_count,
          fb_shares=cp.fb_share_count,
          fb_likes=cp.fb_like_count,
          fb_comments=cp.fb_comment_count,
          fb_clicks=cp.fb_click_count,
          timestamp=now_timestamp
        )
        nrow += 1
    except Exception as e:
      print("Error: CrawlerPage:crawl:\n%s" % e)
    return len(pages)
