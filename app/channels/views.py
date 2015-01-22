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
from app.channels.models import ChannelCounter, Channel
from forms import YoutubeChannelForm

channels_blueprint = Blueprint('channels', __name__, template_folder='templates')

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

@channels_blueprint.route('/fetch_channel_counts')
@login_required
def fetch_channel_counts():
  id = request.args.get('id', None)
  if id is None:
    flash('Error: video counter id is missing!')
    return redirect(url_for('channels.channels_list'))
  cc = ChannelCounter.get(ChannelCounter.id==id)
  if cc.is_runnable():
    # results = Channel.scrape(cc.name, cc.channel)
    results = Channel.scrape(cc)
  else:
    results = {}
  flash("Video counters were updated")
  return redirect(url_for('channels.channels_list'))

@channels_blueprint.route('/channels_summary')
@login_required
def channels_summary():
  id = request.args.get('id', None)
  if id is None:
    flash('Error: id is missing for Video counter summary page!')
    return redirect(url_for('channels.channels_list'))
  cc = ChannelCounter.get(ChannelCounter.id==id)
  channel_name = cc.channel
  counters = Channel.select().where(Channel.name==cc.name).order_by(Channel.timestamp.desc())
  return render_template('channels_summary.html', current_user=current_user,
    counters=counters, id=id, channel_name=channel_name
  )

@channels_blueprint.route('/channels_new')
@login_required
def channels_new():
  form = YoutubeChannelForm()
  return render_template('channel.html', current_user=current_user, form=form, new_counter=True)

@channels_blueprint.route('/channels_create', methods=['POST'])
@login_required
def channels_create():
  form = YoutubeChannelForm(request.form)
  form.validate()
  new_counter = True
  if form.errors:
    pass
  else:
    now = datetime.utcnow()
    counter = ChannelCounter.create(
      name=request.form.get('name'),
      runnable=request.form.get('runnable'),
      gspread_link=request.form.get('gspread_link'),
      channel=None,
      created_at=now,
      updated_at=now
    )
    new_counter = False
    form = YoutubeChannelForm(None, counter)
    flash('Video counter was created')
    return redirect(url_for('channels.channels_list'))
  return render_template('channel.html', current_user=current_user, form=form, new_counter=new_counter)

@channels_blueprint.route('/channels_update', methods=['GET', 'POST'])
@login_required
def channels_update():
  # FIXME ugly code to do both edit/update
  if request.method == 'GET':
    id = request.args.get('id', '')
    counter = ChannelCounter.get(ChannelCounter.id==id)
    form = YoutubeChannelForm(None, counter)
  else:
    id = request.form.get('id')
    counter = ChannelCounter.get(ChannelCounter.id==id)
    form = YoutubeChannelForm(request.form)
    form.validate()
    if form.errors:
      pass
    else:
      now = datetime.utcnow()
      counter.name = request.form.get('name')
      counter.runnable = request.form.get('runnable')
      counter.gspread_link = request.form.get('gspread_link')
      counter.channel = None
      counter.updated_at = now
      counter.save()
      new_counter = False
      form = YoutubeChannelForm(None, counter)
      flash('Video counter was updated')
      return redirect(url_for('channels.channels_list'))
  return render_template('channel.html', current_user=current_user, form=form, new_counter=False, id=id)

@channels_blueprint.route('/channels_list')
@login_required
def channels_list():
  # glink = unicode(c.gspread_link, 'ascii')
  counters = ChannelCounter.select()
  return render_template('channels_list.html', current_user=current_user, counters=counters)
