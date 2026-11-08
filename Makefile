.PHONY: help test lint serve serve-static validate update-readme clean

PYTHON ?= python3

help:
	@echo "CinemaScope — Developer Commands"
	@echo "================================"
	@echo "  make test           Run unit test suite (22 tests)"
	@echo "  make lint           Compile-check all Python modules"
	@echo "  make serve          Start local Flask server on :8080"
	@echo "  make serve-static   Start static HTTP server on :8000"
	@echo "  make validate       Run fast headless integrity validation"
	@echo "  make update-readme  Recompute statistics and regenerate README"
	@echo "  make clean          Clean python bytecode artifacts"

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	$(PYTHON) -m py_compile server.py
	$(PYTHON) -m py_compile scripts/*.py
	$(PYTHON) -m py_compile tests/*.py

serve:
	$(PYTHON) server.py

serve-static:
	@echo "Serving static CinemaScope on http://localhost:8000 ... (Ctrl+C to stop)"
	$(PYTHON) -m http.server 8000

validate: test

update-readme:
	$(PYTHON) scripts/update_readme.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
