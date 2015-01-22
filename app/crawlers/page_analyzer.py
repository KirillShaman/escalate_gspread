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

# Dec 31, 2014:
# modified to work with the Escalate project
# renamed "analyzer.py" to "page_analyzer.py"
# rename "class Page" to "class WebPage"
# see original at: https://github.com/sethblack/python-seo-analyzer/blob/master/analyze.py

# Copyright 2012-2014 Seth Black.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     1. Redistributions of source code must retain the above copyright notice, 
#        this list of conditions and the following disclaimer.
#     2. Redistributions in binary form must reproduce the above copyright 
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#     3. The name of Seth Black may not be used to endorse or promote products
#        derived from this software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# pip install BeautifulSoup4
# pip install nltk

from collections import Counter
from bs4 import BeautifulSoup
from xml.dom import minidom
# from urllib2 import urlopen
# import urllib2
from string import maketrans, punctuation
from operator import itemgetter
from re import sub, match
# these only install on tiny core as sudo and not venv, so don't use it:
# import nltk
# from nltk import stem
from json import loads
import re
import sys
import time
import requests
import urllib
from urlparse import urlparse
from urlparse import urljoin
# if sys.version_info >= (3, 0):
#   from urllib.parse import urlparse
# if sys.version_info < (3, 0) and sys.version_info >= (2, 5):
#   from urlparse import urlparse

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

TOKEN_REGEX = re.compile(r'(?u)\b\w\w+\b')

class Page(object):
  """
  Container for each page and the analyzer.
  """

  def __init__(self, url='', site='', sitemap=None):
    self.url = url
    self.site = site
    self.sitemap = sitemap
    self.add_links = True
    self.pages_to_crawl = []
    self.pages_crawled = []
    self.pages = {}
    self.page_text = ''
    # self.wordcount = {}
    self.wordcount = []
    self.stem_to_word = {}
    # no nltk so can't do:
    # self.stemmer = stem.porter.PorterStemmer()
    self.sorted_words = []
    # FIXME don't rely on urllib and urlparse
    url_parsed = urlparse(self.url)
    self.domain = url_parsed.netloc
    self.title = u''
    self.description = u''
    self.keywords = u''
    self.warnings = []
    self.links = []
    self.googleplusones = 0
    self.twitter_count = 0
    self.fb_total_count = 0
    self.fb_share_count = 0
    self.fb_comment_count = 0
    self.fb_like_count = 0
    self.fb_click_count = 0

    self.translation = maketrans(punctuation, str(u' ' * len(punctuation)).encode('utf-8'))
    super(Page, self).__init__()

  def crawl_and_analyze(self):
    # if sitemap is not None:
    #   page = urlopen(sitemap)
    #   xml_raw = page.read()
    #   xmldoc = minidom.parseString(xml_raw)
    #   urls = xmldoc.getElementsByTagName('loc')
    #   for url in urls:
    #     pages_to_crawl.append(getText(url.childNodes))

    self.pages_to_crawl.append(self.url) # push
    # time.sleep(30) # testing slow crawl
    pages_count = 0
    while len(self.pages_to_crawl) > 0:
      url = self.pages_to_crawl.pop()
      print("\ncrawl_and_analyze: popped url=%s"%url)
      pg = Page(url)
      pages_count += 1
      if pages_count > 1:
        # don't add links after first page crawled, i.e. self.url:
        pg.add_links = False
      #  *******
      pg.analyze()
      #  *******
      print("\ncrawl_and_analyze: pg.pages_crawled=%s"%pg.pages_crawled)
      self.pages_crawled.extend(pg.pages_crawled)
      # avoid crawling a page more than once:
      for apage in pg.pages_to_crawl:
        if apage in self.pages_crawled:
          continue
        else:
          self.pages_to_crawl.extend([apage])
      # pg.sorted_words = sorted(pg.wordcount.iteritems(), key=itemgetter(1), reverse=True)
      # this is already sorted by count:
      pg.sorted_words = pg.wordcount
      yield pg # make this a generator method, so no giant gob of memory is required

  def analyze_a_tags(self, bs):
    """
    Add any new links
    """
    anchors = bs.find_all('a', href=True)
    for tag in anchors:
      if 'title' not in tag:
        self.warn("<a href=\"%s\" ... is missing title attribute" % tag['href'])
      if self.site not in tag['href'] and ':' in tag['href']:
        continue
      # modified_url = self.rel_to_abs_url(tag['href'])
      modified_url = urljoin(self.url, tag['href'])
      self.links.append(modified_url)
      if self.add_links:
        if modified_url in self.pages_crawled:
          continue
        # add more pages to be crawled, but don't 
        # add url's not in this web sites domain:
        modified_url_parsed = urlparse(modified_url)
        modified_url_domain = modified_url_parsed.netloc
        if modified_url_domain == self.domain:
          self.pages_to_crawl.append(modified_url) # push

  def analyze(self):
    """
    Analyze the page and populate attributes
    """
    if self.url in self.pages_crawled:
      return
    self.pages_crawled.append(self.url)
    try:
      # pretend we are firefox and not a spider:
      firefox_header = {'User-agent': 'Mozilla/5.0'}
      page = requests.get(self.url, headers=firefox_header)
      # FIXME handle cookies ?
      page.raise_for_status() # if not 200 raise an exception
    except Exception as e:
      print("\nanalyze: requests.get: error=%s"%e)
      self.warn('analyze: request returned 404: error:\n%s' % e)
      return
    encoding = page.headers['content-type'].split('charset=')[-1]
    if encoding not in('text/html', 'text/plain'):
      try:
        raw_html = unicode(page.text, encoding)
      except:
        self.warn('Can not read {0}'.format(encoding))
        return
    else:
      raw_html = page.text
    # remove comments, to avoid BeautifulSoup hiccups:
    clean_html = sub(r'<!--.*?-->', r'', raw_html.encode('utf-8'), flags=re.DOTALL)
    soup = BeautifulSoup(clean_html)
    texts = soup.findAll(text=True)
    visible_text = filter(self.visible_tags, texts)
    self.process_text(visible_text)
    self.populate(soup)
    self.analyze_title()
    self.analyze_description()
    self.analyze_keywords()
    self.analyze_a_tags(soup)
    self.analyze_img_tags(soup)
    self.analyze_h1_tags(soup)
    self.social_shares()

  def populate(self, bs):
    """
    Populates the instance variables from BeautifulSoup
    """
    try:
      self.title = bs.title.text
    except:
      self.title = ''
      pass
    descr = bs.findAll('meta', attrs={'name':'description'})
    if len(descr) > 0:
      self.description = descr[0].get('content')
    keywords = bs.findAll('meta', attrs={'name':'keywords'})
    if len(keywords) > 0:
      self.keywords = keywords[0].get('content')

  def social_shares(self):
    # google +1's:
    self.googleplusones = 0
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
    }''' % (self.url)
    try:
      respobj = requests.post(api, jobj)
      respobj.raise_for_status()
      adict = respobj.json()
      self.googleplusones = int(adict['result']['metadata']['globalCounts']['count'])
    except requests.exceptions.RequestException as e:
      print("Error: google +1's: requests.exceptions.RequestException: %s"%e)
    except Exception as e:
      # need a logger instead of: print("Error:\n%s"%e)
      print("Error: google +1's: %s"%e)
    # facebook counts, all of them not just shares:
    self.fb_total_count = 0
    self.fb_share_count = 0
    self.fb_comment_count = 0
    self.fb_like_count = 0
    self.fb_click_count = 0
    api = "https://graph.facebook.com/fql?q=SELECT%20like_count,%20total_count,%20share_count,%20click_count,%20comment_count%20FROM%20link_stat%20WHERE%20url%20=%20%27"
    try:
      respobj = requests.get(api + self.url + "%27")
      # responses other than 200 are not considered exceptions, so:
      respobj.raise_for_status()
      adict = respobj.json()
      self.fb_total_count = adict['data'][0]['total_count']
      self.fb_share_count = adict['data'][0]['share_count']
      self.fb_like_count = adict['data'][0]['like_count']
      self.fb_comment_count = adict['data'][0]['comment_count']
      self.fb_click_count = adict['data'][0]['click_count']
    except requests.exceptions.RequestException as e:
      print("Error: facebook: requests.exceptions.RequestException: %s"%e)
    except KeyError as e:
      # need a logger instead of: print("Error:\n%s"%e)
      # print("Error: KeyError: %s"%e)
      pass
    except Exception as e:
      # need a logger instead of: print("Error:\n%s"%e)
      print("Error: facebook: %s"%e)
    # tweets:
    self.twitter_count = 0
    api = "http://urls.api.twitter.com/1/urls/count.json?url="
    try:
      respobj = requests.get(api + self.url)
      # responses other than 200 are not considered exceptions, so:
      respobj.raise_for_status()
      adict = respobj.json()
      self.twitter_count = adict["count"]
    except requests.exceptions.RequestException as e:
      print("Error: tweets: requests.exceptions.RequestException: %s"%e)
      pass
    except Exception as e:
      # need a logger instead of: print("Error:\n%s"%e)
      print("Error: tweets: %s"%e)
      pass

  def translate_non_alphanumerics(self, to_translate, translate_to=u' '):
    not_letters_or_digits = u'!"#%\'()*+,-./:;<=>?@[\]^_`{|}~'
    translate_table = dict((ord(char), translate_to) for char in not_letters_or_digits)
    return to_translate.translate(translate_table)

  def tokenize(self, rawtext):
    return [word for word in TOKEN_REGEX.findall(rawtext.lower()) if word not in ENGLISH_STOP_WORDS]

  def process_text(self, vt):
    self.page_text = ''
    for element in vt:
      self.page_text += element.encode('utf-8').lower() + ' '
    tokens = self.tokenize(self.page_text.decode('utf-8'))
    self.page_text = "\n".join([ll.strip() for ll in self.page_text.splitlines() if ll.strip()])
    # freq_dist = nltk.FreqDist(tokens)
    # for word in freq_dist:
    #   root = self.stemmer.stem_word(word)
    #   if root in self.stem_to_word and freq_dist[word] > self.stem_to_word[root]['count']:
    #     self.stem_to_word[root] = {'word': word, 'count': freq_dist[word]}
    #   else:
    #     self.stem_to_word[root] = {'word': word, 'count': freq_dist[word]}
    #   if root in self.wordcount:
    #     self.wordcount[root] += freq_dist[word]
    #   else:
    #     self.wordcount[root] = freq_dist[word]
    self.wordcount = Counter(tokens).most_common(10)

  def analyze_title(self):
    """
    Validate the title
    """
    t = self.title
    # calculate the length of the title once
    length = len(t)
    if length == 0:
      self.warn('Missing title tag')
    elif length < 10:
      self.warn('Title tag is too short')
    elif length > 70:
      self.warn('Title tag is too long')

  def analyze_description(self):
    """
    Validate the description
    """
    d = self.description
    # calculate the length of the description once
    length = len(d)
    if length == 0:
      self.warn('Missing description')
    elif length < 140:
      self.warn('Description is too short')
    elif length > 255:
      self.warn('Description is too long')

  def analyze_keywords(self):
    """
    Validate keywords
    """
    k = self.keywords
    # calculate the length of keywords once
    length = len(k)
    if length == 0:
      self.warn('Missing keywords')

  def visible_tags(self, element):
    if element.parent.name in ['style', 'script', '[document]']:
      return False
    return True

  def analyze_img_tags(self, bs):
    """
    Verifies that each img has an alt and title
    """
    images = bs.find_all('img')
    for image in images:
      if 'alt' not in image:
        self.warn('Image missing alt')
      if 'title' not in image:
        self.warn('Image missing title')

  def analyze_h1_tags(self, bs):
    """
    Make sure each page has at least one H1 tag
    """
    htags = bs.find_all('h1')
    if len(htags) == 0:
      self.warn('Each page should have at least one h1 tag')

  def rel_to_abs_url(self, link):
    if ':' in link:
      return link
    relative_path = link
    domain = self.url
    if domain[-1] == '/':
      domain = domain[:-1]
    if relative_path[0] != '/':
      relative_path = '/{0}'.format(relative_path)
    return '{0}{1}'.format(domain, relative_path)

  def warn(self, warning):
    self.warnings.append(warning)

  @classmethod
  def getText(self, nodelist):
    """
    Stolen from the minidom documentation
    """
    rc = []
    for node in nodelist:
      if node.nodeType == node.TEXT_NODE:
        rc.append(node.data)
    return ''.join(rc)
