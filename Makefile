.PHONY: help install build package deploy run report all lint test clean

# Default config file
CFG ?= experiments/android_example.yaml

help:
	@echo "OVMobileBench - OpenVINO Benchmarking Pipeline"
	@echo ""
	@echo "Usage: make [target] CFG=path/to/config.yaml"
	@echo ""
	@echo "Targets:"
	@echo "  install    - Install dependencies using poetry"
	@echo "  build      - Build OpenVINO runtime"
	@echo "  package    - Create deployment package"
	@echo "  deploy     - Deploy to device(s)"
	@echo "  run        - Run benchmarks"
	@echo "  report     - Generate reports"
	@echo "  all        - Run complete pipeline"
	@echo "  lint       - Run code linters"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean artifacts"
	@echo "  devices    - List available devices"

install:
	poetry install

build:
	poetry run ovmobilebench build -c $(CFG) --verbose

package:
	poetry run ovmobilebench package -c $(CFG) --verbose

deploy:
	poetry run ovmobilebench deploy -c $(CFG) --verbose

run:
	poetry run ovmobilebench run -c $(CFG) --verbose

report:
	poetry run ovmobilebench report -c $(CFG) --verbose

all:
	poetry run ovmobilebench all -c $(CFG) --verbose

devices:
	poetry run ovmobilebench list-devices

lint:
	poetry run ruff ovmobilebench
	poetry run mypy ovmobilebench

test:
	poetry run pytest tests/ -v

clean:
	rm -rf artifacts/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete