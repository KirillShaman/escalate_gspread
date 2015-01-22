from flask_wtf import Form
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired

class SocialCounterForm(Form):
  # see: app/counters/templates/counter.html
  name = StringField('Name', validators=[DataRequired()])
  runnable = SelectField(u'Run daily', choices=[('yes', 'yes'), ('no', 'no')], default="no", validators=[DataRequired()])
  gspread_link = StringField('Google spreadsheet link', validators=[DataRequired()])
  urls = TextAreaField('URLs')
