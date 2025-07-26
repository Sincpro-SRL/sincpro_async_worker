GEMFURY_PUSH_TOKEN ?= DEFAULT_TOKEN

.SILENT: configure-gemfury

add-gemfury-repo:
	poetry config repositories.fury https://pypi.fury.io/sincpro/

configure-gemfury: add-gemfury-repo
	poetry config http-basic.fury $(GEMFURY_PUSH_TOKEN) NOPASS


install: add-gemfury-repo
	pipx install poetry
	pipx install black
	pipx install autoflake
	pipx install isort
	pipx install pyright
	pipx install pre-commit
	pipx ensurepath
	pre-commit install
	poetry install

ipython:
	poetry run ipython

jupyterlab:
	poetry run jupyter lab

format-yaml:
	@if command -v prettier > /dev/null; then \
		echo "Formatting YAML files with prettier..."; \
		prettier --write "**/*.yml" "**/*.yaml"; \
	else \
		echo "prettier not found. Install with: npm install -g prettier"; \
	fi

format-python:
	poetry run autoflake --in-place --remove-unused-variables --remove-all-unused-imports --ignore-init-module-imports -r sincpro_async_worker
	poetry run autoflake --in-place --remove-unused-variables --remove-all-unused-imports --ignore-init-module-imports -r tests
	poetry run isort sincpro_async_worker
	poetry run isort tests
	poetry run black sincpro_async_worker
	poetry run black tests
	make format-yaml

format: format-python format-yaml

verify-format: format
	@if ! git diff --quiet; then \
	  echo >&2 "✘ El formateo ha modificado archivos. Por favor agrégalos al commit."; \
	  git --no-pager diff --name-only HEAD -- >&2; \
	  exit 1; \
	fi

clean-pyc:
	find . -type d -name '__pycache__' -exec rm -rf {} \; || exit 0
	find . -type f -iname '*.pyc' -delete || exit 0

build: configure-gemfury
	poetry build

publish: configure-gemfury
	poetry publish -r fury --build

test:
	poetry run pytest tests

test_debug:
	poetry run pytest -vvs tests

test_one:
	poetry run pytest ${t} -vvs

type-check:
	poetry run pyright sincpro_logger tests

lint:
	poetry run black --check sincpro_async_worker tests
	poetry run isort --check-only sincpro_async_worker tests
	make type-check

.PHONY: install start clean test build format format-yaml format-all type-check lint 