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
from app.crawlers.models import Crawler, CrawlerPage
from forms import CrawlersForm
from async_crawler import run_spider
import pickle

# This list of English stop words is taken from the "Glasgow Information
# Retrieval Group". The original list can be found at
# http://ir.dcs.gla.ac.uk/resources/linguistic_utils/stop_words
ENGLISH_STOP_WORDS = frozenset([
  "a", "about", "above", "across", "after", "afterwards", "again", "against",
  "all", "almost", "alone", "along", "already", "also", "although", "always",
  "am", "among", "amongst", "amoungst", "amount", "an", "and", "another",
  "any", "anyhow", "anyone", "anything", "anyway", "anywhere", "are",
  "around", "as", "at", "back", "be", "became", "because", "become",
  "becomes", "becoming", "been", "before", "beforehand", "behind", "being",
  "below", "beside", "besides", "between", "beyond", "bill", "both",
  "bottom", "but", "by", "call", "can", "cannot", "cant", "co", "con",
  "could", "couldnt", "cry", "de", "describe", "detail", "do", "done",
  "down", "due", "during", "each", "eg", "eight", "either", "eleven", "else",
  "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone",
  "everything", "everywhere", "except", "few", "fifteen", "fify", "fill",
  "find", "fire", "first", "five", "for", "former", "formerly", "forty",
  "found", "four", "from", "front", "full", "further", "get", "give", "go",
  "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter",
  "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his",
  "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed",
  "interest", "into", "is", "it", "its", "itself", "keep", "last", "latter",
  "latterly", "least", "less", "ltd", "made", "many", "may", "me",
  "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly",
  "move", "much", "must", "my", "myself", "name", "namely", "neither",
  "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone",
  "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on",
  "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our",
  "ours", "ourselves", "out", "over", "own", "part", "per", "perhaps",
  "please", "put", "rather", "re", "same", "see", "seem", "seemed",
  "seeming", "seems", "serious", "several", "she", "should", "show", "side",
  "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone",
  "something", "sometime", "sometimes", "somewhere", "still", "such",
  "system", "take", "ten", "than", "that", "the", "their", "them",
  "themselves", "then", "thence", "there", "thereafter", "thereby",
  "therefore", "therein", "thereupon", "these", "they",
  "third", "this", "those", "though", "three", "through", "throughout",
  "thru", "thus", "to", "together", "too", "top", "toward", "towards",
  "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us",
  "very", "via", "was", "we", "well", "were", "what", "whatever", "when",
  "whence", "whenever", "where", "whereafter", "whereas", "whereby",
  "wherein", "whereupon", "wherever", "whether", "which", "while", "whither",
  "who", "whoever", "whole", "whom", "whose", "why", "will", "with",
  "within", "without", "would", "yet", "you", "your", "yours", "yourself",
  "yourselves"])

crawlers_blueprint = Blueprint('crawlers', __name__, template_folder='templates')

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

@crawlers_blueprint.route('/crawl_site')
@login_required
def crawl_site():
  id = request.args.get('id', None)
  if id is None:
    flash('Error: crawler id is missing!')
    return redirect(url_for('crawlers.crawlers_list'))
  run_spider(flask_app, id)
  time.sleep(1) # wait for spider to awake
  # foreground crawl:
  # crawler = Crawler.query.filter_by(id=id).first()
  # deleted_count = CrawlerPage.query.filter_by(name=crawler.name).delete()
  # resp = db.session.commit()
  # # CrawlerPage.fake_crawl(crawler.name, crawler.url)
  # CrawlerPage.crawl(crawler.name, crawler.url)
  flash("Crawling in progress, please check back later as this may take a while.")
  return redirect(url_for('crawlers.crawlers_list'))

@crawlers_blueprint.route('/crawlers_summary')
@login_required
def crawlers_summary():
  id = request.args.get('id', None)
  if id is None:
    flash('Error: id is missing for Crawler summary page!')
    return redirect(url_for('crawlers.crawlers_list'))
  c = Crawler.get(Crawler.id==id)
  pages = CrawlerPage.select().where(CrawlerPage.name==c.name).order_by(CrawlerPage.timestamp.desc())
  return render_template('crawlers_summary.html', current_user=current_user, pages=pages, id=id)

@crawlers_blueprint.route('/crawled_summary')
@login_required
def crawled_summary():
  id = request.args.get('id', None)
  if id is None:
    flash('Error: id is missing for Crawled summary page!')
    return redirect(url_for('crawlers.crawlers_list'))
  cp = CrawlerPage.get(CrawlerPage.id==id)
  top_ten_sorted_words = pickle.loads(cp.word_freqs)
  return render_template('crawled_summary.html', current_user=current_user, id=id,
    page=cp, words=top_ten_sorted_words[:5]
  )

@crawlers_blueprint.route('/crawlers_new')
@login_required
def crawlers_new():
  form = CrawlersForm()
  return render_template('crawler.html', current_user=current_user, form=form, new_crawler=True)

@crawlers_blueprint.route('/crawlers_create', methods=['POST'])
@login_required
def crawlers_create():
  form = CrawlersForm(request.form)
  form.validate()
  new_crawler = True
  if form.errors:
    pass
  else:
    now = datetime.utcnow()
    crawler = Crawler.create(
      name=request.form.get('name'),
      runnable=request.form.get('runnable'),
      gspread_link=request.form.get('gspread_link'),
      # url=request.form.get('url'),
      url=None,
      crawl_status=None,
      crawled_at=None,
      created_at=now,
      updated_at=now
    )
    new_crawler = False
    form = CrawlersForm(None, crawler)
    flash('Crawler was created')
    return redirect(url_for('crawlers.crawlers_list'))
  return render_template('crawler.html', current_user=current_user, form=form, new_crawler=new_crawler)

@crawlers_blueprint.route('/crawlers_update', methods=['GET', 'POST'])
@login_required
def crawlers_update():
  # FIXME ugly code to do both edit/update
  if request.method == 'GET':
    id = request.args.get('id', '')
    crawler = Crawler.get(Crawler.id==id)
    form = CrawlersForm(None, crawler)
  else:
    id = request.form.get('id')
    crawler = Crawler.get(Crawler.id==id)
    form = CrawlersForm(request.form)
    form.validate()
    if form.errors:
      pass
    else:
      now = datetime.utcnow()
      crawler.name = request.form.get('name')
      crawler.runnable = request.form.get('runnable')
      crawler.gspread_link = request.form.get('gspread_link')
      crawler.url = None
      crawler.updated_at = now
      crawler.save()
      new_crawler = False
      form = CrawlersForm(None, crawler)
      flash('Crawler was updated')
      return redirect(url_for('crawlers.crawlers_list'))
  return render_template('crawler.html', current_user=current_user, form=form, new_crawler=False, id=id)

@crawlers_blueprint.route('/crawlers_list')
@login_required
def crawlers_list():
  crawlers = Crawler.select()
  return render_template('crawlers_list.html', current_user=current_user, crawlers=crawlers)
