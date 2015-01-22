class GUser():
  # note: this is not a db model, so it's only in memory
  def __init__(self, id, gmail, gpassword):
    self.id = id
    self.gmail = gmail
    self.gpassword = gpassword

  def is_authenticated(self):
    return True

  def is_active(self):
    return True

  def is_anonymous(self):
    return False

  def get_id(self):
    return int(self.id)
    # try:
    #   return unicode(self.id)  # python 2
    # except NameError:
    #   return str(self.id)  # python 3

  def __repr__(self):
    return '<id={} gmail={}'.format(self.id, self.gmail)
