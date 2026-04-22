.PHONY: help install dev test run lint format clean

help:
	@echo "Mutation Seam - Available Commands"
	@echo ""
	@echo "install    - Install production dependencies"
	@echo "dev        - Install development dependencies"
	@echo "test       - Run test suite"
	@echo "test-v     - Run tests with verbose output"
	@echo "run        - Start the development server"
	@echo "lint       - Run linting checks"
	@echo "format     - Format code with black and isort"
	@echo "clean      - Remove build artifacts and cache"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install black isort flake8 mypy

test:
	pytest tests/ -q

test-v:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html

run:
	python -m uvicorn app.main:app --reload --port 8000

lint:
	flake8 app tests
	mypy app

format:
	black app tests
	isort app tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov dist build *.egg-info

.DEFAULT_GOAL := help
