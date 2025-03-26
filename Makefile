VENV_DIR = venv
PYTHON = python3
REQ_FILE = requirements.txt

help:
	@echo "Available commands:"
	@echo ""
	@echo "  make venv               - Create a Python virtual environment"
	@echo "  make install            - Install dependencies from requirements.txt"
	@echo "  make activate           - Show activation command for the virtual environment"
	@echo "  make clean              - Remove the virtual environment"
	@echo "  make ingest-bls         - Run the BLS ingestion module"
	@echo "  make ingest-population  - Run the Population ingestion module"
	@echo "  make run-analysis       - Run the analysis module"
	@echo "  make help               - Show available commands"

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
	@${PYTHON} -m src.ingest.bls

ingest-population:
	@${PYTHON} -m src.ingest.population

run-analysis:
	@${PYTHON} -m src.analyze.analysis

.PHONY: venv install activate clean run
