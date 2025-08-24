import unittest
import datetime
from unittest.mock import patch, MagicMock
import json

from submitobs import get_mime_type, parse_arguments, main, SubmitRequestData


class TestSubmitObs(unittest.TestCase):

    def test_mime_types(self):
        cases = [
            ["file.png", "image/png"],
            ["FILE.PNG", "image/png"],
            ["too.many.dots.PnG", "image/png"],
            ["failure.log", "text/plain"],
            ["success.txt", "text/plain"],
            ["wojak.jpg", "image/jpeg"],
            ["doge.JPEG", "image/jpeg"],
            ["extensionless", "application/octet-stream"],
            ["unknownext.tkis", "application/octet-stream"]
        ]

        for case in cases:
            self.assertEqual(get_mime_type(case[0]), case[1])

    def test_parse_arguments_basic(self):
        """Test basic argument parsing with required arguments only."""
        args = ["image.png", "NOAA 15", "2023-01-01T12:00:00Z"]
        parsed = parse_arguments(args)

        self.assertEqual(parsed.filename, "image.png")
        self.assertEqual(parsed.sat_name, "NOAA 15")
        self.assertEqual(parsed.aos, "2023-01-01T12:00:00Z")
        self.assertIsNone(parsed.tca)
        self.assertIsNone(parsed.los)
        self.assertEqual(parsed.metadata, "{}")
        self.assertIsNone(parsed.rating)

    def test_parse_arguments_with_optional(self):
        """Test argument parsing with all optional arguments."""
        args = [
            "image1.png,image2.png",
            "NOAA 18",
            "2023-01-01T12:00:00Z",
            "--tca", "2023-01-01T12:30:00Z",
            "--los", "2023-01-01T13:00:00Z",
            "--metadata", '{"notes": "test observation"}',
            "--rating", "0.8"
        ]
        parsed = parse_arguments(args)

        self.assertEqual(parsed.filename, "image1.png,image2.png")
        self.assertEqual(parsed.sat_name, "NOAA 18")
        self.assertEqual(parsed.aos, "2023-01-01T12:00:00Z")
        self.assertEqual(parsed.tca, "2023-01-01T12:30:00Z")
        self.assertEqual(parsed.los, "2023-01-01T13:00:00Z")
        self.assertEqual(parsed.metadata, '{"notes": "test observation"}')
        self.assertEqual(parsed.rating, 0.8)

    def test_parse_arguments_comma_separated_files(self):
        """Test parsing comma-separated filenames."""
        args = ["file1.png,file2.jpg,file3.txt", "NOAA 19", "2023-01-01T12:00:00Z"]
        parsed = parse_arguments(args)

        self.assertEqual(parsed.filename, "file1.png,file2.jpg,file3.txt")

    def test_parse_arguments_help(self):
        """Test that help argument is available."""
        args = ["--help"]

        # This should raise SystemExit when --help is used
        with self.assertRaises(SystemExit):
            parse_arguments(args)

    def test_main_success_basic(self):
        """Test main function with basic arguments."""
        args = ["image.png", "NOAA 15", "2023-01-01T12:00:00Z"]

        with patch('submitobs.submit_observation') as mock_submit:
            mock_submit.return_value = {"status-code": 201, "response-text": "Success"}

            result = main(args)
            self.assertEqual(result, 0)

            # Verify submit_observation was called with correct data
            mock_submit.assert_called_once()
            call_args = mock_submit.call_args[0][0]
            self.assertIsInstance(call_args, SubmitRequestData)
            self.assertEqual(call_args.image_path, ["image.png"])
            self.assertEqual(call_args.sat_name, "NOAA 15")

    def test_main_success_with_optional_args(self):
        """Test main function with optional arguments."""
        args = [
            "image.png",
            "NOAA 18",
            "2023-01-01T12:00:00Z",
            "--tca", "2023-01-01T12:30:00Z",
            "--los", "2023-01-01T13:00:00Z",
            "--metadata", '{"notes": "test"}',
            "--rating", "0.9"
        ]

        with patch('submitobs.submit_observation') as mock_submit:
            mock_submit.return_value = {"status-code": 204, "response-text": "Success"}

            result = main(args)
            self.assertEqual(result, 0)

            # Verify submit_observation was called with correct data
            call_args = mock_submit.call_args[0][0]
            # Create timezone-aware datetime objects for comparison
            tca_time = datetime.datetime(2023, 1, 1, 12, 30, 0, tzinfo=datetime.timezone.utc)
            los_time = datetime.datetime(2023, 1, 1, 13, 0, 0, tzinfo=datetime.timezone.utc)
            self.assertEqual(call_args.tca, tca_time)
            self.assertEqual(call_args.los, los_time)
            self.assertEqual(call_args.config, '{"notes": "test"}')
            self.assertEqual(call_args.rating, 0.9)

    def test_main_failure_status(self):
        """Test main function returns failure exit code for unsuccessful submission."""
        args = ["image.png", "NOAA 15", "2023-01-01T12:00:00Z"]

        with patch('submitobs.submit_observation') as mock_submit:
            mock_submit.return_value = {"status-code": 400, "response-text": "Bad Request"}

            result = main(args)
            self.assertEqual(result, 1)

    def test_main_invalid_json_metadata(self):
        """Test main function handles invalid JSON metadata."""
        args = ["image.png", "NOAA 15", "2023-01-01T12:00:00Z", "--metadata", "invalid json"]

        result = main(args)
        self.assertEqual(result, 1)

    def test_main_comma_separated_files(self):
        """Test main function handles comma-separated filenames correctly."""
        args = ["file1.png,file2.jpg", "NOAA 15", "2023-01-01T12:00:00Z"]

        with patch('submitobs.submit_observation') as mock_submit:
            mock_submit.return_value = {"status-code": 201, "response-text": "Success"}

            result = main(args)
            self.assertEqual(result, 0)

            # Verify filenames are properly split
            call_args = mock_submit.call_args[0][0]
            self.assertEqual(call_args.image_path, ["file1.png", "file2.jpg"])

    def test_main_default_tca_los(self):
        """Test that TCA and LOS default to AOS when not specified."""
        args = ["image.png", "NOAA 15", "2023-01-01T12:00:00Z"]

        with patch('submitobs.submit_observation') as mock_submit:
            mock_submit.return_value = {"status-code": 201, "response-text": "Success"}

            result = main(args)
            self.assertEqual(result, 0)

            # Verify TCA and LOS default to AOS
            call_args = mock_submit.call_args[0][0]
            # Create timezone-aware datetime object for comparison
            aos_time = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
            self.assertEqual(call_args.aos, aos_time)
            self.assertEqual(call_args.tca, aos_time)
            self.assertEqual(call_args.los, aos_time)

    def test_main_exception_handling(self):
        """Test that main function handles exceptions gracefully."""
        args = ["image.png", "NOAA 15", "2023-01-01T12:00:00Z"]

        with patch('submitobs.submit_observation') as mock_submit:
            mock_submit.side_effect = Exception("Test exception")

            result = main(args)
            self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()
