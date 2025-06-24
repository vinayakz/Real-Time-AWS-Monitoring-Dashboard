# Makefile for AWS CloudWatch Log Analyzer

.PHONY: help install install-dev test lint format clean run docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code"
	@echo "  clean        Clean up generated files"
	@echo "  run          Run the Streamlit application"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run Docker container"

# Installation
install:
	pip install -r requirements/requirements.txt

install-dev:
	pip install -r requirements/requirements-dev.txt
	pre-commit install

# Testing
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 src/ tests/
	mypy src/
	bandit -r src/

format:
	black src/ tests/
	isort src/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Run application
run:
	streamlit run src/main.py

# Docker commands
docker-build:
	docker build -t aws-cloudwatch-analyzer .

docker-run:
	docker run -p 8501:8501 \
		-e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
		-e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
		-e AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} \
		aws-cloudwatch-analyzer

# Development workflow
dev-setup: install-dev
	@echo "Development environment setup complete!"

check: lint test
	@echo "All checks passed!"

# CI/CD helpers
ci-test:
	pytest tests/ --junitxml=test-results.xml --cov=src --cov-report=xml

# Documentation
docs:
	cd docs && sphinx-build -b html . _build/html

# Package management
freeze:
	pip freeze > requirements/requirements-frozen.txt

# Security check
security:
	bandit -r src/ -f json -o security-report.json

# Performance profiling
profile:
	python -m cProfile -o profile.stats src/main.py
