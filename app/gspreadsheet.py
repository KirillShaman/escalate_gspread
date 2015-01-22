# see: http://www.indjango.com/access-google-sheets-in-python-using-gspread/
# This will issue 100 HTTP requests to Google API:
# for row in range(1, 101):
#     worksheet.update_cell(1, row, 'Bingo!')
# While this is only two HTTP requests:

# cell_list = worksheet.range('A1:A100')
# for cell in cell_list:
#     cell.value = 'Bingo!'
# worksheet.update_cells(cell_list)
# Spreadsheets API is not very fast so good advice would be to reduce underlying HTTP requests as much as you can.

# I've just added a new method for Worksheet: export(). 
# It will allow you to request your CSV data right from a Google API server bypassing gspread's data processing. 
# It should be faster, so please try it and share your results. 
# I haven't released the update on PyPI yet, so you have to check out the master branch from GitHub for the new code.
# That way, your code snippet for downloading a worksheet may look like this:
# def fetch_sheet(sheet, id):
#     spreadsheet = client.open_by_key(id)
#     worksheet = spreadsheet.worksheets()[0]
#     csv_data = worksheet.export(format='csv').read()
#     with open('sheets/%s.csv' % sheet, 'w') as f:
#         f.write(csv_data)
# You can omit format argument in export call as it defaults to 'csv'. 'pdf' and 'tsv' values work as well.

import gspread

class Gspreadsheet():

  def __init__(self, user, password, url):
    self.user = user
    self.password = password
    self.url = url
    self.gclient = None

  def login(self):
    try:
      self.gclient = gspread.login(self.user, self.password)
    except Exception as e:
      print("Error:")
      print(e)
      self.gclient = None
    return self.gclient

  def get_row(self, wks, row):
    return wks.row_values(row)

  def col_one(self, wks):
    # note: ".row_count" seems to always equal 1,000 rows,
    #       so be sure to break on the first empty row during processing:
    cell_list = wks.range("A2:A%s" % wks.row_count)
    params = []
    for cell in cell_list:
      if len(cell.value) > 0:
        params.append(cell.value)
      else:
        break
    return params
