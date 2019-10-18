""" s3 support for remote file interactivity """
import os
from typing import IO, Any, Optional, Tuple
from urllib.parse import urlparse as parse_url

from pandas.compat._optional import import_optional_dependency

from pandas._typing import FilePathOrBuffer

s3fs = import_optional_dependency(
    "s3fs", extra="The s3fs package is required to handle s3 files."
)


def _strip_schema(url):
    """Returns the url without the s3:// part"""
    result = parse_url(url, allow_fragments=False)
    return result.netloc + result.path


def get_file_and_filesystem(
    filepath_or_buffer: FilePathOrBuffer, mode: Optional[str] = None
) -> Tuple[IO, Any]:
    from botocore.exceptions import NoCredentialsError

    if mode is None:
        mode = "rb"

    # Support customised S3 servers endpoint URL via environment variable
    # The S3_ENDPOINT should be the complete URL to S3 service following
    # the format: http(s)://{host}:{port}
    s3_endpoint = os.environ.get("S3_ENDPOINT")
    client_kwargs: Optional[Dict[str, str]] = {
        "endpoint_url": s3_endpoint
    } if s3_endpoint else None
    fs = s3fs.S3FileSystem(anon=False, client_kwargs=client_kwargs)
    try:
        file = fs.open(_strip_schema(filepath_or_buffer), mode)
    except (FileNotFoundError, NoCredentialsError):
        # boto3 has troubles when trying to access a public file
        # when credentialed...
        # An OSError is raised if you have credentials, but they
        # aren't valid for that bucket.
        # A NoCredentialsError is raised if you don't have creds
        # for that bucket.
        fs = s3fs.S3FileSystem(anon=True, client_kwargs=client_kwargs)
        file = fs.open(_strip_schema(filepath_or_buffer), mode)
    return file, fs


def get_filepath_or_buffer(
    filepath_or_buffer: FilePathOrBuffer,
    encoding: Optional[str] = None,
    compression: Optional[str] = None,
    mode: Optional[str] = None,
) -> Tuple[IO, Optional[str], Optional[str], bool]:
    file, _fs = get_file_and_filesystem(filepath_or_buffer, mode=mode)
    return file, None, compression, True
