from flask_wtf import Form
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired

class MozscapeForm(Form):
  name = StringField('Name', validators=[DataRequired()])
  runnable = SelectField(u'Runnable', choices=[('yes', 'yes'), ('no', 'no')], default="no", validators=[DataRequired()])
  gspread_link = StringField('Google spreadsheet link', validators=[DataRequired()])
  urls = TextAreaField('URLs')
