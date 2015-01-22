from flask_wtf import Form
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired

class YoutubeChannelForm(Form):
  name = StringField('Name', validators=[DataRequired()])
  runnable = SelectField(u'Runnable', choices=[('yes', 'yes'), ('no', 'no')], default="no", validators=[DataRequired()])
  gspread_link = StringField('Google spreadsheet link', validators=[DataRequired()])
  channel = StringField('Channel')
