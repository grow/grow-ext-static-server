deploy:
	gcloud app deploy \
	  -q \
	  --project=$(project) \
	  --version=$(version) \
	  --verbosity=error \
	  --promote \
	  app.yaml

run:
	dev_appserver.py --allow_skipped_files=true --port=9999 .