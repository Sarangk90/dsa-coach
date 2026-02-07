.PHONY: test lint format typecheck check run dashboard clean

test:
	pytest
lint:
	ruff check . --fix
format:
	ruff format .
typecheck:
	mypy dsa_coach/
check: lint format typecheck test
run:
	python coach.py
dashboard:
	python coach.py dashboard
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage
