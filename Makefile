POETRY ?= poetry
PYTHON ?= $(POETRY) run python

.PHONY: lint
lint: mypy black

.PHONY: test
test:
	$(PYTHON) -m pytest

.PHONY: mypy
mypy:
	$(POETRY) run mypy .

.PHONY: black
black:
	$(POETRY) run black .
