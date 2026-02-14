.PHONY: docs deploy depoly

docs:
	python scripts/gen_mkdocs.py

deploy: docs
	mkdocs gh-deploy

depoly: deploy
