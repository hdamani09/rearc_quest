module "rearc_sqs" {
    source = "./modules/sqs"
    queue_name = "s3-event-notifications-queue"
    app-env = var.env
}

module "rearc_s3" {
    source = "./modules/s3"
    bucket_name = "rearc-bucket"
    app-env = var.env
}

module "rearc_s3_config_file_upload" {
    source = "./modules/s3_object"
    bucket_id = module.rearc_s3.bucket_id
    bucket_key = "config/aws-config.yaml"
    file_path = "../aws-config.yaml"
}

module "rearc_s3_event_notification" {
    source = "./modules/s3_event"
    s3_bucket_id = module.rearc_s3.bucket_id
    sqs_queue_arn = module.rearc_sqs.queue_arn
    s3_prefix = "data/population/raw/"
}

module "rearc_s3_sqs_policy" {
  source        = "./modules/s3_sqs_policy"
  sqs_queue_url = module.rearc_sqs.queue_url
  sqs_queue_arn = module.rearc_sqs.queue_arn
  s3_bucket_arn = module.rearc_s3.bucket_arn
}

module "rearc_iam_role_lambda" {
    source = "./modules/iam"
    role_name = "lambda-iam"
    identifiers = ["lambda.amazonaws.com"]
    app-env = var.env
}

module "rearc_lambda_sqs_policy" {
    source = "./modules/iam_policy"
    iam_role_id = module.rearc_iam_role_lambda.iam_role_id
    policy_name = "lambda_sqs"
    action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
    effect = "Allow"
    resource = module.rearc_sqs.queue_arn
    app-env = var.env
}

module "rearc_lambda_s3_list_bucket_policy" {
    source = "./modules/iam_policy"
    iam_role_id = module.rearc_iam_role_lambda.iam_role_id
    policy_name = "lambda_s3_list_bucket"
    action = [
            "s3:ListBucket"
        ]
    effect = "Allow"
    resource = module.rearc_s3.bucket_arn
    app-env = var.env
}

module "rearc_lambda_s3_object_policy" {
    source = "./modules/iam_policy"
    iam_role_id = module.rearc_iam_role_lambda.iam_role_id
    policy_name = "lambda_s3_object"
    action = [
            "s3:PutObject",
            "s3:GetObject",
            "s3:DeleteObject",
        ]
    effect = "Allow"
    resource = "${module.rearc_s3.bucket_arn}/*"
    app-env = var.env
}

module "rearc_lambda_cloudwatch_policy" {
    source = "./modules/iam_policy"
    iam_role_id = module.rearc_iam_role_lambda.iam_role_id
    policy_name = "lambda_cloudwatch"
    action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
    effect = "Allow"
    resource = "*"
    app-env = var.env
}

module "rearc_lambda" {
  source = "./modules/lambda"
  iam_role_arn = module.rearc_iam_role_lambda.iam_role_arn
  function_name = "rearc-lambda"
  dependencies_package_path = "../artifacts/lambda_layers.zip"
  function_package_path = "../artifacts/lambda_function.zip"
  handler_path = "src.main.lambda_handler"
  python_runtime = "python3.13"
  runtime_config_path = module.rearc_s3_config_file_upload.s3_uri
  app-env = var.env
}

module "rearc_sqs_lambda_event_mapping" {
    source = "./modules/sqs_lambda_event"
    sqs_queue_arn = module.rearc_sqs.queue_arn
    lambda_arn = module.rearc_lambda.lambda_arn
    app-env = var.env
}

module "rearc_daily_lambda_trigger_event" {
    source = "./modules/eventbridge_lambda"
    schedule_cron = "cron(0 15 * * ? *)"
    lambda_function_arn = module.rearc_lambda.lambda_arn
    lambda_function_name = module.rearc_lambda.lambda_function_name
    app-env = var.env
}