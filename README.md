This project was built as part of the Northcoders bootcamp.

There is a function which gets quotes from api.quotable.io/. 
The function is designed to be deployed as an AWS lambda function via terraform.

The terraform build includes:
1. Creating two buckets - one to store code (lambda and layer) and one to store quotes obtained by the function
2. Building the lambda and supporting layer
3. Creating a cloudwatch event scheduler to run the lambda regularly
4. Setting up a metric filter, sns topic and metric alarm to send "GREAT QUOTES" obtained by the function
   to an email address.
5. Creating an IAM role and required policies for the above to function.
