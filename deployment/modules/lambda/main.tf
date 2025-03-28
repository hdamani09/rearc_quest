# Lambda Layer for dependencies
resource "aws_lambda_layer_version" "dependencies_layer" {
  filename   = var.dependencies_package_path
  layer_name = "${var.function_name}-dependencies"

  compatible_runtimes = [var.python_runtime]
  source_code_hash = filemd5(var.dependencies_package_path)
}

resource "aws_lambda_function" "lambda_function" {
  filename      = var.function_package_path
  function_name = "${var.app-env}-${var.function_name}"
  role          = var.iam_role_arn
  handler       = var.handler_path
  timeout = 120

  layers = [
    aws_lambda_layer_version.dependencies_layer.arn,
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python313:1"
  ]

  source_code_hash = filemd5(var.function_package_path)
  runtime = var.python_runtime

  # Pass the aws_config.yaml path as env variable to lambda
  environment {
    variables = {
      config_path = var.runtime_config_path
    }
  }

  tags = {
    env = var.app-env
  }
}