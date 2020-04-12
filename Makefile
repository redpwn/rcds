POETRY ?= poetry
PYTHON ?= $(POETRY) run python

.PHONY: lint
lint: black flake8 mypy

.PHONY: test
test:
	$(PYTHON) -m pytest

.PHONY: cover
cover:
	$(POETRY) run coverage run -m pytest

.PHONY: mypy
mypy:
	$(POETRY) run mypy .

.PHONY: black
black:
	$(POETRY) run black .

.PHONY: flake8
flake8:
	$(POETRY) run flake8 .

.PHONY: htmlcov
htmlcov: cover
	$(POETRY) run coverage html
