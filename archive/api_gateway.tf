resource "aws_api_gateway_rest_api" "moonratbrains" {
  name        = "MoonratBrains"
  description = "Terraform Serverless Slack Bot"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = "${aws_api_gateway_rest_api.moonratbrains.id}"
  resource_id = "${aws_api_gateway_method.eventhandler.resource_id}"
  http_method = "${aws_api_gateway_method.eventhandler.http_method}"

  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = "${aws_lambda_function.lambdafunc.invoke_arn}"
}

resource "aws_api_gateway_method_response" "200" {
  rest_api_id = "${aws_api_gateway_rest_api.moonratbrains.id}"
  resource_id = "${aws_api_gateway_resource.eventhandler.id}"
  http_method = "${aws_api_gateway_method.eventhandler.http_method}"
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "integrationResponse" {
  depends_on = ["aws_api_gateway_integration.lambda"]
  rest_api_id = "${aws_api_gateway_rest_api.moonratbrains.id}"
  resource_id = "${aws_api_gateway_resource.eventhandler.id}"
  http_method = "${aws_api_gateway_method.eventhandler.http_method}"
  status_code = "${aws_api_gateway_method_response.200.status_code}"

}
resource "aws_api_gateway_deployment" "apigwdeployment" {
  depends_on = ["aws_api_gateway_integration.lambda"]
  rest_api_id = "${aws_api_gateway_rest_api.moonratbrains.id}"
  stage_name  = "test"
}

output "base_url" {
  value = "${aws_api_gateway_deployment.apigwdeployment.invoke_url}"
}