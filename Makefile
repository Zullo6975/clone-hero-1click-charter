run:
	python -m charter.cli

lint:
	ruff charter

test:
	pytest
