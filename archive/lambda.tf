variable "bot_token" {}
variable "coinmarketcap_token" {}

resource "aws_lambda_function" "lambdafunc" {
  function_name = "handleMoonratEvent"

  # The bucket name as created earlier with "aws s3api create-bucket"
  s3_bucket = "lambda-function-package-bucket"
  s3_key    = "v1.0.0/PythonPackage.zip"

  # "main" is the filename within the zip file (main.js) and "handler"
  # is the name of the property under which the handler function was
  # exported in that file.
  handler = "moonratv2.lambda_handler"
  runtime = "python3.6"

  role = "${aws_iam_role.lambda_exec.arn}"

  environment {
      variables {
          BOT_TOKEN="${var.bot_token}",
          COINMARKETCAP_API_TOKEN="${var.coinmarketcap_token}"
      }
  }
}

# IAM role which dictates what other AWS services the Lambda function
# may access.
resource "aws_iam_role" "lambda_exec" {
  name = "handleMoonratDirectEvent_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_api_gateway_resource" "eventhandler" {
  rest_api_id = "${aws_api_gateway_rest_api.moonratbrains.id}"
  parent_id   = "${aws_api_gateway_rest_api.moonratbrains.root_resource_id}"
  path_part   = "event-handler"
}

resource "aws_api_gateway_method" "eventhandler" {
  rest_api_id   = "${aws_api_gateway_rest_api.moonratbrains.id}"
  resource_id   = "${aws_api_gateway_resource.eventhandler.id}"
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.lambdafunc.arn}"
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_deployment.apigwdeployment.execution_arn}/*/*"
}