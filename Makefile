.PHONY: help install build package deploy run report all lint test clean

# Default config file
CFG ?= experiments/android_example.yaml

help:
	@echo "OVMobileBench - OpenVINO Benchmarking Pipeline"
	@echo ""
	@echo "Usage: make [target] CFG=path/to/config.yaml"
	@echo ""
	@echo "Targets:"
	@echo "  install    - Install dependencies using pip"
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
	pip install -r requirements.txt
	pip install -e .

build:
	ovmobilebench build -c $(CFG) --verbose

package:
	ovmobilebench package -c $(CFG) --verbose

deploy:
	ovmobilebench deploy -c $(CFG) --verbose

run:
	ovmobilebench run -c $(CFG) --verbose

report:
	ovmobilebench report -c $(CFG) --verbose

all:
	ovmobilebench all -c $(CFG) --verbose

devices:
	ovmobilebench list-devices

lint:
	pre-commit run --all-files

test:
	pytest tests/ -v

test-e2e:
	# E2E tests moved to helpers directory as utility scripts
	@echo "E2E scripts are now in helpers/ directory"

clean:
	rm -rf artifacts/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
