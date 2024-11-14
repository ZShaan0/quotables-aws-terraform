import pytest
from unittest.mock import Mock, patch
from requests import Response
from moto import mock_aws
import os
import boto3
from freezegun import freeze_time
import logging
import json

with patch.dict(os.environ, {"S3_BUCKET_NAME": "test_bucket"}):
    from src.quotes import get_quote, URL, write_to_s3, lambda_handler


class DummyContext:
    pass


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_SECURITY_TOKEN"] = "test"
    os.environ["AWS_SESSION_TOKEN"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture(scope="function")
def s3(aws_credentials):
    with mock_aws():
        yield boto3.client("s3", region_name="eu-west-1")


@pytest.fixture
def bucket(s3):
    s3.create_bucket(
        Bucket="test_bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )


quotes = [
    {
        "_id": "KBBVyoNtUib6",
        "content": "Most great people have attained their greatest success ",
        "author": "Napoleon Hill",
        "tags": ["Success"],
        "authorSlug": "napoleon-hill",
        "length": 99,
        "dateAdded": "2020-01-15",
        "dateModified": "2023-04-14",
    },
    {
        "_id": "UQ2TjZ5IIDSR",
        "content": "Anyone who doesn't take truth seriously in small matters.",
        "author": "Albert Einstein",
        "tags": ["Famous Quotes"],
        "authorSlug": "albert-einstein",
        "length": 96,
        "dateAdded": "2020-02-22",
        "dateModified": "2023-04-14",
    },
    {
        "_id": "iqob_h7AuhiT",
        "content": "Only through our connectedness to others can we really know.",
        "author": "Harriet Lerner",
        "tags": ["Famous Quotes"],
        "authorSlug": "harriet-lerner",
        "length": 171,
        "dateAdded": "2020-01-26",
        "dateModified": "2023-04-14",
    },
]

processed = {
    "content": "Most great people have attained their greatest success ",
    "author": "Napoleon Hill",
    "length": 99,
}


class TestGetQuote:
    """Tests the get_quote helper."""

    def test_get_quote_returns_status_and_formatted_dict(self):
        mock_response = Mock(spec=Response, status_code=200)
        with patch("src.quotes.requests.get") as mock_request:
            mock_request.return_value = mock_response
            mock_response.json.return_value = quotes[0:1]
            assert get_quote() == (200, processed)

    def test_get_quote_calls_requests_with_correct_url(self):
        with patch("src.quotes.requests.get") as mock_request:
            get_quote()
            mock_request.assert_called_once_with(URL)

    def test_get_quote_valid_url(self):
        status_code, _ = get_quote()
        assert status_code == 200

class TestWriteToS3:
    """Tests the write_to_s3 helper."""

    def test_write_to_s3(self, s3, bucket):
        key = "test_file.json"
        data = [{"a": 1}, {"b": 2}]
        resp = write_to_s3(s3, data, "test_bucket", key)
        listing = s3.list_objects_v2(Bucket="test_bucket")
        assert len(listing["Contents"]) == 1
        assert listing["Contents"][0]["Key"] == "test_file.json"
        assert resp

    def test_write_s3_logs_client_error(self, s3, bucket, caplog):
        key = "test_file.json"
        data = [{"a": 1}, {"b": 2}]
        with caplog.at_level(logging.INFO):
            resp = write_to_s3(s3, data, "test_bucket2", key)
            assert not resp
            assert "ClientError" in caplog.text


class TestHandler:
    """Tests the lambda handler"""

    @patch("src.quotes.get_quote")
    def test_handler_writes_quotes_to_s3(self, mock_quote, s3, bucket, caplog):
        mock_quote.side_effect = zip([200] * 3, quotes)
        event = {}
        context = DummyContext()
        with caplog.at_level(logging.INFO):
            lambda_handler(event, context)
            assert "Wrote quotes to S3" in caplog.text

    @freeze_time("2024-04-01 12:00")
    @patch("src.quotes.get_quote")
    def test_handler_writes_quotes_to_s3_partial(self, mock_quote, s3, bucket, caplog):
        mock_quote.side_effect = zip([200, 200, 404], quotes)
        event = {}
        context = DummyContext()
        with caplog.at_level(logging.INFO):
            lambda_handler(event, context)
            expected_key = "quote_1711972800.json"
            obj = s3.get_object(Bucket="test_bucket", Key=expected_key)["Body"]
            expected = {"quotes": quotes[:2]}
            assert json.loads(obj.read()) == expected
            assert "Wrote quotes to S3" in caplog.text

    @patch("src.quotes.write_to_s3")
    @patch("src.quotes.get_quote")
    def test_handler_handles_client_error(
        self, mock_quote, mock_write, s3, bucket, caplog
    ):
        mock_quote.side_effect = zip([200] * 3, quotes)
        mock_write.return_value = False
        event = {}
        context = DummyContext()
        with caplog.at_level(logging.INFO):
            lambda_handler(event, context)
            assert "There was a problem. Quotes not written." in caplog.text

    @patch("src.quotes.get_quote")
    def test_handler_handles_unexpected(self, mock_quote, s3, bucket, caplog):
        mock_quote.side_effect = ArithmeticError
        event = {}
        context = DummyContext()
        with caplog.at_level(logging.INFO):
            lambda_handler(event, context)
            assert "Unexpected Exception: " in caplog.text

    @patch("src.quotes.get_quote")
    @patch("src.quotes.random", return_value=0.05)
    def test_flags_great_quotes(self, mock_random, mock_quote, s3, bucket, caplog):
        mock_quote.side_effect = zip([200] * 3, quotes)
        event = {}
        context = DummyContext()
        with caplog.at_level(logging.INFO):
            lambda_handler(event, context)
            assert "[GREAT QUOTE]" in caplog.text
