#!/usr/bin/env python3
import argparse
import datetime
import os
import requests
import sys
import logging
import json

# This is awfully early. However, some of the later imports seem to define the basic config on its own.
if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, format="%(levelname)s %(asctime)s - %(message)s", level=logging.DEBUG)

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from utils.configuration import open_config
from utils.dates import from_iso_format
from hmac_token import get_authorization_header_value
from orbitdb import OrbitDatabase

config = open_config()
section = config["server"]
station_id = str(section["id"])
secret = bytearray.fromhex(section["secret"])
url = section["url"]


@dataclass
class SubmitRequestData:
    """
    Request data for send to server.

    Parameters
    ==========
    image_path: str
        List of files to upload
    sat_name: str
        Satellite name compatible with NORAD format
    aos: datetime.datetime
        Acquisition of Signal (or Satellite)
    tca: datetime.datetime
        Time of Closest Approach
    los: datetime.datetime
        Loss of Signal (or Satellite)
    config: dict
        meta-data information in JSON format
    rating: float?
        Rating of image
    """
    image_path: List[str]
    sat_name: str
    aos: datetime.datetime
    tca: datetime.datetime
    los: datetime.datetime
    config: Optional[str]
    rating: Optional[float]


def get_tle(sat_name: str, date: datetime.datetime) -> Optional[List[str]]:
    try:
        db = OrbitDatabase()
        return db.get_tle(sat_name, date)
    except Exception:
        return None


def get_mime_type(filename: str) -> str:
    """
    Returns the MIME type for known and unknown file formats.

    Parameters
    ==========
    filename: str
        name of the file to be sent
    return:
        MIME type as str
    """

    # This is a list of file types that possibly could make sense in the Svarog project.
    # When adding new types, don't forget to update ALLOWED_FILE_TYPES in
    # server/app/controllers/receive.py
    known_types = {
        ".csv": "text/plain",
        ".gif": "image/gif",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".json": "application/json",
        ".log": "text/plain",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".txt": "text/plain",
        ".wav": "audio/wav"
    }

    txt = filename.lower()
    ext = os.path.splitext(txt)[1]
    return known_types.get(ext, "application/octet-stream")


def submit_observation(data: SubmitRequestData):
    '''
    Attempts to submit the observation to the content server.

    Parameters
    ==========
    data: SubmitRequestData
        Observation to be sent (image, sat_name, etc.)
    return:
        dict with an extended status (successful, observation id, extra details etc.)
    '''
    form_data = {
        "aos": data.aos.isoformat(),
        "tca": data.tca.isoformat(),
        "los": data.los.isoformat(),
        "sat": data.sat_name,
        "rating": data.rating,
        "config": data.config
    }

    tle = get_tle(data.sat_name, data.aos)
    if tle is not None:
        form_data["tle"] = tle

    # Now process the files
    files = {}
    cnt = 0
    body: Dict[str, Any] = {
    }
    for path in data.image_path:
        _, filename = os.path.split(path)

        # If there's only one file, it will use "file" key. The second file will be "file1",
        # third "file2" etc.
        file_key = "file" if cnt == 0 else f"file{cnt}"

        file_obj = open(path, 'rb')
        body[file_key] = file_obj

        files[file_key] = (filename, file_obj, get_mime_type(filename), {})
        cnt = cnt + 1

    body.update(form_data)

    header_value = get_authorization_header_value(station_id,
                                                  secret, body, datetime.datetime.utcnow())

    headers = {
        "Authorization": header_value
    }

    # Check if notes are a valid JSON
    logging.debug(f"Meta-data = {data.config}")

    logging.info(f"Submitting observation, url={url}, file(s)={data.image_path}")

    try:
        resp = requests.post(url, form_data, headers=headers, files=files)
    except requests.exceptions.ConnectionError:
        return {
            "status-code": 0,
            "response-text": f"Unable to connect to {url}, connection refused"
        }
    if (resp.status_code >= 400):
        logging.warning("Response status: %d" % resp.status_code)
    else:
        logging.info("Response status: %d" % resp.status_code)

    # Logging extra details in case of failed submission.
    status = {
        "status-code": resp.status_code,
        "upload-time": datetime.datetime.now().isoformat(),
        "response-text": resp.text
    }

    if resp.status_code not in [201, 204]:
        # On info, just log the field names in what we sent. On debug, log also the content and the whole response.
        logging.info("Submission details: headers: %s, form: %s" % (",".join(headers.keys()), ",".join(form_data.keys())))
        logging.debug("headers=%s" % headers)
        logging.debug("form=%s" % form_data)
        logging.debug("Response details: %s" % resp.text)
    else:
        logging.info(f"Upload successful: {resp.text}")

    # All seems to be OK
    return status


def parse_arguments(args=None):
    """
    Parse command line arguments using argparse.

    Parameters
    ==========
    args: list, optional
        List of arguments to parse. If None, uses sys.argv[1:]

    Returns
    =======
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Submit observation data to Svarog station server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s image.png "NOAA 15" 2023-01-01T12:00:00Z
  %(prog)s image1.png,image2.png "NOAA 18" 2023-01-01T12:00:00Z --tca 2023-01-01T12:30:00Z
  %(prog)s image.png "NOAA 19" 2023-01-01T12:00:00Z --metadata '{"notes": "test"}' --rating 0.8
        """
    )

    parser.add_argument(
        "filename",
        help="File(s) to upload. Can be a single file or comma-separated list (no spaces)"
    )

    parser.add_argument(
        "sat_name",
        help="Satellite name compatible with NORAD format"
    )

    parser.add_argument(
        "aos",
        help="Acquisition of Signal (or Satellite) time in ISO format"
    )

    parser.add_argument(
        "--tca",
        help="Time of Closest Approach in ISO format (defaults to AOS if not specified)"
    )

    parser.add_argument(
        "--los",
        help="Loss of Signal (or Satellite) time in ISO format (defaults to AOS if not specified)"
    )

    parser.add_argument(
        "--metadata",
        default="{}",
        help="Metadata information in JSON format (default: empty JSON object)"
    )

    parser.add_argument(
        "--rating",
        type=float,
        help="Rating of image (0.0 to 1.0)"
    )

    return parser.parse_args(args)


def main(args=None):
    """
    Main function that can be called programmatically or from command line.

    Parameters
    ==========
    args: list, optional
        Command line arguments. If None, uses sys.argv[1:]

    Returns
    =======
    int
        Exit code (0 for success, 1 for failure)
    """
    try:
        parsed_args = parse_arguments(args)

        # Parse filenames (can be comma-separated)
        filenames = [f.strip() for f in parsed_args.filename.split(",")]

        # Parse dates
        aos = from_iso_format(parsed_args.aos)
        tca = from_iso_format(parsed_args.tca) if parsed_args.tca else aos
        los = from_iso_format(parsed_args.los) if parsed_args.los else aos

        # Validate metadata JSON
        try:
            json.loads(parsed_args.metadata)
            cfg = parsed_args.metadata
        except json.JSONDecodeError:
            logging.error(f"ERROR: The metadata '{parsed_args.metadata}' is not valid JSON")
            return 1

        # Create submission data
        data = SubmitRequestData(
            image_path=filenames,
            sat_name=parsed_args.sat_name,
            aos=aos,
            tca=tca,
            los=los,
            config=cfg,
            rating=parsed_args.rating
        )

        # Submit observation
        status = submit_observation(data)

        # Return appropriate exit code
        return 0 if status["status-code"] in [201, 204] else 1

    except Exception as e:
        logging.error(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
