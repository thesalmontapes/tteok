init:
	pip install -r requirements.txt
init-dev:
	pip install -r requirements_dev.txt
lint:
	flake8 && mypy .
