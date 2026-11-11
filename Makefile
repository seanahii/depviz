PYTHON ?= python3

.PHONY: test run clean

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

run:
	./run.sh $(ARGS)

clean:
	rm -rf build dist *.egg-info .pytest_cache out
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
