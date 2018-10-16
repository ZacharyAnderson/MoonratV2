variable "bot_token" {}

resource "aws_lambda_function" "dev" {
  function_name = "handleMoonrateEvent"

  # The bucket name as created earlier with "aws s3api create-bucket"
  s3_bucket = "lambda-function-package-bucket"
  s3_key    = "v1.0.0/PythonPackage.zip"

  # "main" is the filename within the zip file (main.js) and "handler"
  # is the name of the property under which the handler function was
  # exported in that file.
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"

  role = "${aws_iam_role.lambda_exec.arn}"

  environment {
      variables {
          BOT_TOKEN="${var.bot_token}"
      }
  }
}

# IAM role which dictates what other AWS services the Lambda function
# may access.
resource "aws_iam_role" "lambda_exec" {
  name = "handleMoonrateDirectEvent_role"

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