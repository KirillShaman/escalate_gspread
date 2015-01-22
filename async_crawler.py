import os
from app import datetime, time, db
from app.crawlers.models import Crawler, CrawlerPage
from decorators import async

@async
def async_spider(app, crawler_id):
  now = datetime.utcnow()
  print("%s async_spider started..." % datetime.utcnow())
  print("\tPID=%s" % os.getpid())
  print("\tcrawler_id=%s" % crawler_id)
  crawler = Crawler.get(Crawler.id==crawler_id)
  if crawler.is_runnable:
    # delete crawled pages before crawling it again:
    dq = CrawlerPage.delete().where(CrawlerPage.name==crawler.name)
    deleted_count = dq.execute()
    crawler.crawled_at = now
    crawler.crawl_status = 'crawling'
    crawler.save()
    # time.sleep(10) # simulate a lot of crawling
    pages_len = CrawlerPage.crawl(crawler)
    crawler.crawl_status = "crawled %s pages" % pages_len
    crawler.save()
    print("\tnumber of pages crawled=%s"%pages_len)
  print("%s async_spider ended" % datetime.utcnow())

def run_spider(app, crawler_id):
  print("\nrun_spider=%s" % crawler_id)
  async_spider(app, crawler_id)
