from itertools import *
import requests
import bs4

# put non user funcs here, outside of the class
#   these are functions/methods used by user funcs:
def spammed(text):
  return "spam " + text

class UserDefinedFunctions(object):
  """ User functions:
        - must use the @staticmethod decorator, so these funcs can be seen by "dir" and "getattr"
        - must begin with "user_"
        - must return an array/list of dict's, so the result can be serialized/stored
  """

  @staticmethod
  def user_google_suggest(keywords):
    url = "http://google.com/complete/search?output=toolbar&q=%s" % keywords
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text)
    results = soup.findAll("suggestion")
    suggestions = []
    for result in results:
      result_attrs = dict(result.attrs)
      suggestions.append(result_attrs)
    # limit suggestions to the 1st 5:
    return suggestions[:5]

  @staticmethod
  def user_spammer(text1, text2):
    # simple example
    return [
      {"text1": "spam and " + text1},
      {"text2": "spam spam " + text2 + " and spam"}
    ]

  @staticmethod
  def user_spam_me(text_to_spam):
    # example that calls a non user function/method:
    with_spam = spammed(text_to_spam)
    return [ {"text_to_spam": with_spam} ]
