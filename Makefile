VENV_DIR = venv
PYTHON = python3.13
REQ_FILE = requirements.txt
CONFIG ?= local-config.yaml

LAMBDA_VENV_DIR = python
LAMBDA_FUNCTION_DIR = src
PACKAGE_DIR = artifacts
DEPENDENCIES_PACKAGE_NAME = lambda_layers.zip
FUNCTION_PACKAGE_NAME = lambda_function.zip

DEPLOYMENT_DIR = deployment

help:
	@echo "Available commands:"
	@echo ""
	@echo "  make venv                          			- Create a Python virtual environment"
	@echo "  make install                       			- Install dependencies from requirements.txt"
	@echo "  make activate                      			- Show activation command for virtual env"
	@echo "  make clean                         			- Remove the virtual environment"
	@echo "  make ingest-bls CONFIG=local-config.yaml       	- Run the BLS ingestion module"
	@echo "  make ingest-population CONFIG=local-config.yaml 	- Run the Population ingestion module"
	@echo "  make run-analysis CONFIG=local-config.yaml     	- Run the analysis module"
	@echo "  make package                          		- Creates lambda_function.zip & lambda_layers.zip for deployment"
	@echo "  make deploy                          			- Deploys the terraform scripts to AWS infra"
	@echo "  make help                          			- Show available commands"


venv:
	@echo "Creating virtual environment..."
	@${PYTHON} -m venv ${VENV_DIR}
	@echo "Virtual environment created at ${VENV_DIR}"

install: venv
	@echo "Installing dependencies..."
	@${VENV_DIR}/bin/pip install --upgrade pip
	@${VENV_DIR}/bin/pip install -r ${REQ_FILE}
	@echo "Dependencies installed successfully."

activate:
	@echo "Run the following command to activate the virtual environment:"
	@echo "source ${VENV_DIR}/bin/activate"

clean:
	@echo "Removing virtual environment..."
	@rm -rf ${VENV_DIR}
	@echo "Virtual environment removed."

ingest-bls:
	@${PYTHON} -m src.ingest.bls --config ${CONFIG}

ingest-population:
	@${PYTHON} -m src.ingest.population --config ${CONFIG}

run-analysis:
	@${PYTHON} -m src.analyze.analysis --config ${CONFIG}

package:
	zip -g $(FUNCTION_PACKAGE_NAME) -r ${LAMBDA_FUNCTION_DIR}
	mv $(FUNCTION_PACKAGE_NAME) $(PACKAGE_DIR)/

	$(PYTHON) -m venv $(LAMBDA_VENV_DIR)
	$(LAMBDA_VENV_DIR)/bin/pip install -U pip
	$(LAMBDA_VENV_DIR)/bin/pip install -r base-requirements.txt

	# Make the package light by removing irrelevant files
	rm -rf $(LAMBDA_VENV_DIR)/bin
	rm -rf $(LAMBDA_VENV_DIR)/etc
	rm -rf $(LAMBDA_VENV_DIR)/include
	rm $(LAMBDA_VENV_DIR)/pyvenv.cfg
	cd $(LAMBDA_VENV_DIR)/lib/$(PYTHON)/site-packages
	cd $(CURDIR)

	# Adding python packages
	zip -qr $(DEPENDENCIES_PACKAGE_NAME) $(LAMBDA_VENV_DIR)/
	rm -rf ${LAMBDA_VENV_DIR}
	mv $(DEPENDENCIES_PACKAGE_NAME) $(PACKAGE_DIR)/

deploy:
	cd $(DEPLOYMENT_DIR)
	terraform apply


.PHONY: venv install activate clean ingest-bls ingest-population run-analysis package deploy