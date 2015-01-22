# result from running:
# pwiz.py -e sqlite app/seo.db > seo_models.py

from peewee import *

db = SqliteDatabase('seo.db', **{})

# class ChannelCounter(Model):
#   channel = CharField()
#   created_at = DateTimeField(null=True)
#   name = CharField()
#   runnable = CharField()
#   updated_at = DateTimeField(null=True)

#   class Meta:
#     db = db
#     db_table = 'channel_counters'

# class ChannelCount(Model):
#   channel = CharField()
#   dislikes = IntegerField(null=True)
#   likes = IntegerField(null=True)
#   name = CharField()
#   timestamp = DateTimeField(null=True)
#   title = CharField(null=True)
#   url = CharField()
#   views = IntegerField(null=True)

#   class Meta:
#     db = db
#     db_table = 'channel_counts'

# class CrawledPage(Model):
#   a_tags = CharField(null=True)
#   fb_clicks = IntegerField(null=True)
#   fb_comments = IntegerField(null=True)
#   fb_likes = IntegerField(null=True)
#   fb_shares = IntegerField(null=True)
#   fb_total = IntegerField(null=True)
#   google_plusses = IntegerField(null=True)
#   h1_tag = CharField(null=True)
#   img_tags = CharField(null=True)
#   meta_description = CharField(null=True)
#   meta_keywords = CharField(null=True)
#   name = CharField(null=True)
#   plain_text = TextField(null=True)
#   sitemap = CharField(null=True)
#   timestamp = DateTimeField(null=True)
#   title_tag = CharField(null=True)
#   tweets = IntegerField(null=True)
#   url = CharField(null=True)
#   warnings = CharField(null=True)
#   word_freqs = TextField(null=True)

#   class Meta:
#     db = db
#     db_table = 'crawled_pages'

# class Crawler(Model):
#   crawl_status = CharField(null=True)
#   crawled_at = DateTimeField(null=True)
#   created_at = DateTimeField(null=True)
#   name = CharField()
#   runnable = CharField()
#   updated_at = DateTimeField(null=True)
#   url = CharField()

#   class Meta:
#     db = db
#     db_table = 'crawlers'

# class FunctionResult(Model):
#   fr_function = CharField()
#   fr_name = CharField()
#   fr_params = CharField()
#   fr_results = BlobField(null=True)
#   fr_tag = CharField()
#   fr_timestamp = DateTimeField(null=True)

#   class Meta:
#     db = db
#     db_table = 'function_results'

class SocialCounter(Model):
  created_at = DateTimeField(null=True)
  name = CharField()
  runnable = CharField()
  updated_at = DateTimeField(null=True)
  urls = CharField()

  class Meta:
    database = db
    db_table = 'social_counters'

# class SocialCount(Model):
#   fb_clicks = IntegerField(null=True)
#   fb_comments = IntegerField(null=True)
#   fb_likes = IntegerField(null=True)
#   fb_shares = IntegerField(null=True)
#   fb_total = IntegerField(null=True)
#   google_plusses = IntegerField(null=True)
#   name = CharField()
#   timestamp = DateTimeField(null=True)
#   tweets = IntegerField(null=True)
#   url = CharField()

#   class Meta:
#     db = db
#     db_table = 'social_counts'

# class UserFunction(Model):
#   uf_created_at = DateTimeField(null=True)
#   uf_function = CharField()
#   uf_name = CharField()
#   uf_params = CharField()
#   uf_runnable = CharField()
#   uf_updated_at = DateTimeField(null=True)

#   class Meta:
#     db = db
#     db_table = 'user_functions'

class User(Model):
  email = CharField()
  password_digest = CharField(null=True)
  username = CharField()

  class Meta:
    database = db
    db_table = 'users'

