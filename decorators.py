# 2015jan8: this works and returns immediately, but
#           it is probably not a good idea for lots
#           of crawl requests
from threading import Thread
def async(f):
  def wrapper(*args, **kwargs):
    thr = Thread(target=f, args=args, kwargs=kwargs)
    thr.start()
  return wrapper

# 2015jan8: the following hangs on any call to "requests.get(...)":
# from multiprocessing import Process
# def async(f):
#   def wrapper(*args, **kwargs):
#     p = Process(target=f, args=args)
#     p.start() # run f in a process in the background
#   return wrapper

# python 3+ only, so not sure if it works:
# import multiprocessing as mp
# def async(f):
#   def wrapper(*args, **kwargs):
#     mp.set_start_method('spawn')
#     q = mp.Queue()
#     p = mp.Process(target=f, args=args)
#     p.start() # run f in a process in the background
#   return wrapper
