# Escalate

> A ready-to-use SEO tool based on ideas from [Pipulate](https://github.com/miklevin/pipulate "Pipulate"),
but more advanced, and this **python flask** app uses both **SQLite** and **Google spreadsheets** for data storage.

> Escalate was designed for use with [Levinux](https://github.com/miklevin/levinux "Levinux")
or [Tiny Core](http://distro.ibiblio.org/tinycorelinux/ "Tiny Core"), but may be used on any 
platform with python.

> The app also provides several export formats to download data for use in Excel or other spreadsheet apps.

> The Elasticsearch version of Escalate has moved to https://github.com/cleesmith/escalate_with_elasticsearch,
but is no longer under development as it's inappropriate for tiny *nix's.

***
***

[Crawler video](http://youtu.be/rMLXLh3FG-M "Crawler video")

***

![Crawler screeshot](/screenshots/crawler_results_spreadsheet.png?raw=true "Crawler screeshot")

***
***

## Getting started

### Levinux

#### on a mac os x you can increase memory and open another port
```
nano Pipulate.app/Contents/Resources/qemuonmac.sh ... to look like this:
cd ../MacOS
./i386-softmmu \
-m 512 \
-kernel vmlinuz \
-initrd core.gz \
-hda home.qcow \
-hdb opt.qcow \
-hdc tce.qcow \
-tftp ../../../Reset/Server \
-redir tcp:2222::22 \
-redir tcp:8080::80 \
-redir tcp:8888::8888 \
-redir tcp:5000::5000 \
-append "quiet noautologin loglevel=3 home=sda1 opt=sdb1 tce=sdc1"
```

#### setup this app and run it
```
start levinux
perform option 1 to install pipulate, so we have git and python installed
restart levinux
ssh tc@localhost -p 2222
git clone https://github.com/cleesmith/escalate_gspread.git
cd escalate_gspread

... setup virtualenv, which includes pip and app isolation even after reboots:
cd ~
curl -O https://pypi.python.org/packages/source/v/virtualenv/virtualenv-12.0.5.tar.gz
tar xzf virtualenv-12.0.5.tar.gz
rm -rf virtualenv-12.0.5.tar.gz
cd escalate_gspread
python ~/virtualenv-12.0.5/virtualenv.py escalate_gspread

... always do the following after "cd escalate_gspread" so all requirements are found:
source escalate_gspread/bin/activate
... to verify:
pip --version

pip install -r requirements.txt

mv config.py.CHANGE_ME config.py
... to generate a SECRET_KEY do this:
python
  import os
  r = os.urandom(128)
  r.encode('base-64')
... copy/paste into config.py
vi config.py
... also, ensure the following are correct:
  DATABASE = 'seo.db'
  GSPREAD_USER = '???'
  GSPREAD_PASSWORD = '???'

python manage.py db_create

nohup python manage.py waitress_please &
in chrome, safari, firefox browse to http://localhost:5000
```

#### double check everything still works after a reboot:
```
sudo poweroff
restart levinux
ssh tc@localhost -p 2222
cd escalate_gspread
source escalate_gspread/bin/activate
nohup python manage.py waitress_please &
in chrome, safari, firefox browse to http://localhost:5000
```

#### if desired you may start the background job scheduler:
```
nohup python manage.py jobs &
vi jobs.py ... to alter or code new jobs
```

***

### Windows

> use the Levinux instructions above

***

### Mac OS X

#### setup this app and run
```
git clone https://github.com/cleesmith/escalate_gspread.git
cd escalate_gspread
pip install -r requirements.txt

mv config.py.CHANGE_ME config.py
... to generate a SECRET_KEY do this:
python
  import os
  r = os.urandom(128)
  r.encode('base-64')
... copy/paste into config.py
nano config.py
... also, ensure the following are correct:
  DATABASE = 'seo.db'
  GSPREAD_USER = '???'
  GSPREAD_PASSWORD = '???'

python manage.py db_create
python manage.py runserver
```

***

### Ubuntu/Debian

#### Python
assuming python 2.7.6 is installed already
```
sudo apt-get install python-dev
sudo apt-get install python-setuptools
sudo apt-get install python-pip
```

> the following is highly recommended when working on several apps on the same machine, as it keeps apps isolated from each other (think zoo):

```
pip install virtualenvwrapper
nano ~/.bash_profile
    ... add:
    source /usr/local/bin/virtualenvwrapper.sh
source ~/.bash_profile
cd escalate_gspread
mkvirtualenv escalate_gspread
deactivate
workon escalate_gspread
```

#### setup this app and run
```
sudo apt-get install git
git clone https://github.com/cleesmith/escalate_gspread.git
```

./start_prod``` for normal usage, or ```./start``` if you're coding, or:
```
cd escalate_gspread
pip install -r requirements.txt

mv config.py.CHANGE_ME config.py
... to generate a SECRET_KEY do this:
python
  import os
  r = os.urandom(128)
  r.encode('base-64')
... copy/paste into config.py
nano config.py
... also, ensure the following are correct:
  DATABASE = 'seo.db'
  GSPREAD_USER = '???'
  GSPREAD_PASSWORD = '???'

python manage.py db_create
cd testing ... start a test web site in background:
nohup python -m SimpleHTTPServer 8888 &
cd .. 
... start escalate web app in background:
nohup gunicorn -b 0.0.0.0:80 run:flask_app &
... start job scheduler in background:
nohup python manage.py jobs &
```

***
***
