resource "aws_s3_bucket" "b" {
  bucket = "lambda-function-package-bucket"
  acl    = "private"

  tags {
    Name        = "Ricks bucket"
    Environment = "Dev"
  }
}