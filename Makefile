.PHONY: build deploy build_package

TAG?=$(shell git rev-list HEAD --max-count=1 --abbrev-commit)
export TAG

build_package:
	zip -r9 $(TAG).zip ~/moonratV2/venv/lib/python3.6/site-packages
	zip -r9 -g $(TAG).zip ~/moonratV2/venv/lib64/python3.6/site-packages
	zip -g $(TAG).zip moonratv2.py

build: build_package
	aws s3 cp $(TAG).zip s3://lambda-function-package-bucket
