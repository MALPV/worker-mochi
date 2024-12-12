"""Test the Vercel Blob Storage integration.

This test verifies that:
1. We can connect to Vercel Blob Storage
2. We can upload files
3. We can list existing blobs
4. The response format matches what our handler expects

Requirements:
    - .env file with BLOB_READ_WRITE_TOKEN set (for integration tests)
    - vercel-blob package must be installed
"""

import logging
import os
from pathlib import Path
from typing import NoReturn
from unittest.mock import patch, Mock
from urllib.parse import urlparse
import tempfile
import json

import pytest
import vercel_blob
from dotenv import load_dotenv
from src.handler import upload_file_to_uploadthing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


@pytest.fixture
def mock_video_file():
    """Create a temporary mock video file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        # Write some dummy video data
        tmp_file.write(b'fake video content')
        tmp_file.flush()
        yield Path(tmp_file.name)
    # Cleanup after test
    if os.path.exists(tmp_file.name):
        os.remove(tmp_file.name)


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv('UPLOADTHING_API_KEY', 'fake_api_key')


def test_upload_file_to_uploadthing_success(mock_video_file, mock_env):
    """Test successful file upload to UploadThing."""
    # Mock the presigned response
    mock_presigned_response = Mock()
    mock_presigned_response.json.return_value = {
        "data": [{
            "url": "https://fake-upload-url.com",
            "fields": {"key": "value"},
            "fileUrl": "https://fake-file-url.com/video.mp4"
        }]
    }

    # Mock the upload response
    mock_upload_response = Mock()
    
    # Set up the mock responses
    with patch('requests.post') as mock_post:
        mock_post.side_effect = [mock_presigned_response, mock_upload_response]
        
        # Call the function
        presigned_resp, upload_resp, file_name = upload_file_to_uploadthing(mock_video_file)
        
        # Verify the function called the API correctly
        assert mock_post.call_count == 2
        
        # Verify first call (presigned URL request)
        first_call = mock_post.call_args_list[0]
        assert first_call[0][0] == "https://api.uploadthing.com/v6/uploadFiles"
        assert first_call[1]["headers"] == {"x-uploadthing-api-key": "fake_api_key"}
        
        # Verify the responses
        assert presigned_resp == mock_presigned_response
        assert upload_resp == mock_upload_response
        assert file_name.endswith('.mp4')


def test_upload_file_to_uploadthing_missing_api_key(mock_video_file, monkeypatch):
    """Test upload fails when API key is missing."""
    # Ensure the environment variable is not set
    monkeypatch.delenv('UPLOADTHING_API_KEY', raising=False)
    
    with pytest.raises(ValueError, match="UPLOADTHING_API_KEY environment variable not set"):
        upload_file_to_uploadthing(mock_video_file)


def test_upload_file_to_uploadthing_retry_logic(mock_video_file, mock_env):
    """Test retry logic when upload fails initially."""
    print("\nTesting retry logic...")
    
    # Mock responses
    mock_success_response = Mock()
    mock_success_response.json.return_value = {
        "data": [{
            "url": "https://fake-upload-url.com",
            "fields": {"key": "value"},
            "fileUrl": "https://utfs.io/f/fake-success-url.mp4"
        }]
    }
    
    # First two attempts fail, third succeeds
    with patch('requests.post') as mock_post:
        mock_post.side_effect = [
            Exception("Network error - First attempt"),  # First attempt fails
            Exception("Network error - Second attempt"), # Second attempt fails
            mock_success_response,                       # Third attempt succeeds (presigned)
            Mock()                                      # Upload succeeds
        ]
        
        with patch('time.sleep') as mock_sleep:  # Don't actually sleep in tests
            print("\nAttempting upload with retry logic...")
            presigned_resp, upload_resp, file_name = upload_file_to_uploadthing(
                mock_video_file,
                max_retries=2,
                initial_delay=1.0
            )
            
            # Verify retry delays
            print("\nVerifying retry delays:")
            delay_calls = [args[0] for args, _ in mock_sleep.call_args_list]
            print(f"- First retry delay: {delay_calls[0]} seconds")
            print(f"- Second retry delay: {delay_calls[1]} seconds")
            assert delay_calls == [1.0, 2.0], "Incorrect retry delays"
            
            # Verify number of attempts
            print(f"\nTotal attempts made: {mock_post.call_count}")
            assert mock_post.call_count == 4, "Should have made exactly 4 attempts (2 fails, 1 success presigned, 1 upload)"
            
            # Verify final result
            assert presigned_resp == mock_success_response
            print("\nUpload eventually succeeded after retries!")


def test_upload_file_to_uploadthing_max_retries_exceeded(mock_video_file, mock_env):
    """Test that function raises error after max retries are exceeded."""
    print("\nTesting max retries exceeded...")
    
    with patch('requests.post') as mock_post:
        # All attempts will fail
        mock_post.side_effect = [
            Exception("Network error - First attempt"),
            Exception("Network error - Second attempt"),
            Exception("Network error - Third attempt (final)")
        ]
        
        with patch('time.sleep') as mock_sleep:
            print("\nAttempting upload (expected to fail)...")
            with pytest.raises(Exception) as exc_info:
                upload_file_to_uploadthing(
                    mock_video_file,
                    max_retries=2,
                    initial_delay=1.0
                )
            
            # Verify retry delays
            delay_calls = [args[0] for args, _ in mock_sleep.call_args_list]
            print(f"\nRetry delays used: {delay_calls}")
            assert len(delay_calls) == 2, "Should have attempted 2 retries"
            
            # Verify error message
            print(f"\nFinal error: {str(exc_info.value)}")
            assert "Network error - Third attempt (final)" in str(exc_info.value)
            print("\nTest passed: Upload failed after exhausting all retries")


@pytest.mark.integration
def test_upload_file_to_uploadthing_real():
    """Test actual file upload to UploadThing.
    
    This test requires UPLOADTHING_API_KEY to be set in the environment.
    It will actually upload a file to UploadThing.
    """
    if not os.getenv('UPLOADTHING_API_KEY'):
        pytest.skip("UPLOADTHING_API_KEY not set")

    # Create a test video file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        # Create a small video-like file (100KB of random data)
        tmp_file.write(os.urandom(100 * 1024))
        tmp_file.flush()
        file_path = Path(tmp_file.name)

    try:
        print("\nStarting upload test...")
        # Perform the actual upload
        presigned_resp, upload_resp, file_name = upload_file_to_uploadthing(file_path)
        
        print("\n=== RAW RESPONSE DATA ===")
        print("\nPresigned Response Object:", presigned_resp)
        print("\nPresigned Response Raw Text:", presigned_resp.text)
        print("\nUpload Response Object:", upload_resp)
        print("\nUpload Response Raw Text:", upload_resp.text)
        print("\nFile Name:", file_name)
        
        # Extract and verify URLs
        response_data = presigned_resp.json()
        file_url = response_data['data'][0]['fileUrl']
        app_url = response_data['data'][0]['appUrl']
        
        print("\n=== URL COMPARISON ===")
        print("\nDirect CDN URL (fileUrl):")
        print(f"  {file_url}")
        print("  - Direct access through CDN")
        print("  - Faster delivery")
        print("  - No authentication required")
        print("  - Best for public video sharing")
        
        print("\nAuthenticated URL (appUrl):")
        print(f"  {app_url}")
        print("  - Goes through your app configuration")
        print("  - Can have additional security")
        print("  - May have rate limiting")
        print("  - Best for protected content")
        
        print("\nRecommendation: Use fileUrl for the video generation app")
        print("=========================")
        
        # Verify the response
        assert 'data' in response_data, "No 'data' in response"
        assert len(response_data['data']) > 0, "Empty data array in response"
        assert 'fileUrl' in response_data['data'][0], "No fileUrl in response"
        
        # Verify the file URL is accessible
        assert file_url.startswith('https://')
        
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)


def main() -> NoReturn:
    """Run the integration test directly."""
    import sys

    if not os.getenv("BLOB_READ_WRITE_TOKEN"):
        logger.error("BLOB_READ_WRITE_TOKEN environment variable not set")
        logger.error("Please create a .env file with BLOB_READ_WRITE_TOKEN=your-token")
        sys.exit(1)

    test_blob_storage_integration()
    sys.exit(0)


if __name__ == "__main__":
    main()
