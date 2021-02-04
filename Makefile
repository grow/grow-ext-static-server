.PHONY: test
test:
	pipenv run python -m grow_static_server.main_test

curl-test:
	GROW_STATIC_SERVER_POD_ROOT=test \
	  pipenv run gunicorn -b :9999 -w 2 grow_static_server.main:app &
	sleep 4s
	curl http://localhost:9999/
	curl http://localhost:9999/assets/cat.jpg > /dev/null
	curl http://localhost:9999/sitemap.xml
	pkill -f gunicorn

install:
	pipenv install -d
