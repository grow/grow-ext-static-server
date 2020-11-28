.PHONY: test
test:
	pipenv run python -m grow_static_server.main_test

install:
	pipenv install -d
