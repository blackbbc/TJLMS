git pull origin master
cd src
kill -9 `cat tjlms.pid`
gunicorn app:app -p tjlms.pid -b 127.0.0.1:12450 -D
