from flask_wtf import Form
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from user_defined_functions import UserDefinedFunctions
import inspect

class UserFunctionForm(Form):
  name = StringField('Name', validators=[DataRequired()])
  runnable = SelectField(u'Auto run', choices=[('yes', 'yes'), ('no', 'no')], default="no", validators=[DataRequired()])
  params = TextAreaField('Params')
  gspread_link = StringField('Google spreadsheet link', validators=[DataRequired()])

  funcs = []
  list_user_funcs = dir(UserDefinedFunctions)
  user_funcs = [(uf,uf) for uf in list_user_funcs if "user_" in uf]
  for func in user_funcs:
    # get the args for this function:
    args_list = inspect.getargspec(getattr(UserDefinedFunctions, func[0]))[0]
    # args_list.remove('cls') # as 'cls', class, isn't really an arg for class methods
    select_option = "%s(%s)" % (func[0], ', '.join(args_list))
    aselect = (select_option, select_option)
    funcs.append(aselect)

  function = SelectField(u'Auto run', choices=funcs, validators=[DataRequired()])
