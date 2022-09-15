.PHONY: docs/serve
docs/serve:
	mkdocs serve

.PHONY: scan
scan:
	bandit -r .

.PHONY: flake8
flake8:
	flake8