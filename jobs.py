from app import datetime
from app.counters.models import SocialCounter, SocialCount
from app.channels.models import ChannelCounter, Channel
from app.crawlers.models import Crawler, CrawlerPage

def social_counters():
  social_counters = SocialCounter.select()
  for sc in social_counters:
    if sc.is_runnable():
      processed = SocialCount.fetch_counters(sc.name, sc.urls)
  print("%s job: social counters processed" % datetime.utcnow())

def youtube_channels():
  counters = ChannelCounter.select()
  for c in counters:
    if c.is_runnable():
      processed = Channel.scrape(c.name, c.urls)
  print("%s job: youtube channels processed" % datetime.utcnow())

def crawlers():
  crawlers = Crawler.select()
  for crawler in crawlers:
    if crawler.is_runnable():
      # delete crawler before crawling it again:
      dq = CrawlerPage.delete().where(CrawlerPage.name==crawler.name)
      deleted_count = dq.execute()
      pages = CrawlerPage.crawl(crawler)
  print("%s job: crawlers processed" % datetime.utcnow())
