import json
import os
import sys
import logging
from src.ingest.bls import main as bls_handler
from src.ingest.population import main as population_handler
from src.analyze.analysis import main as analysis_handler
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda handler function.

    :param event: The event dictionary containing input parameters.
    :param context: AWS Lambda execution context (not used here).
    :return: A response dictionary indicating success or failure.
    """

    try:
        trigger_source = detect_trigger_source(event)
        logger.info(f"Trigger Source: {trigger_source}")

        config_path = os.environ.get('config_path')
        run_type = 'analyze' if trigger_source == 'SQS' else 'ingest'

        logger.info(f"Received config_path: {config_path}")
        logger.info(f"Received run_type: {run_type}")

        if run_type == 'ingest':
            bls_handler(config_path)
            population_handler(config_path)
        else:
            analysis_handler(config_path)

        response = {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Lambda executed successfully",
                "config_path": config_path,
                "run_type": run_type
            })
        }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        response = {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }

    return response

def detect_trigger_source(event: Dict[str, Any]) -> str:
    """
    Detect the source of the Lambda trigger.
    
    Args:
        event (dict): Event payload
    
    Returns:
        str: Trigger source identifier
    """
    # Check for SQS trigger
    if 'Records' in event and event['Records'][0].get('eventSource') == 'aws:sqs':
        return 'SQS'
    else:
        return 'Other'