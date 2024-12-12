# Contributing to worker-mochi

Thank you for your interest in contributing to worker-mochi! This document provides guidelines and instructions for contributing.

## Prerequisites

- Python 3.10 or higher
- CUDA-compatible GPU
- Docker (for container builds)

## Development Setup

1. Fork and clone the repository:

   ```bash
   git clone https://github.com/runpod-workers/worker-mochi.git
   cd worker-mochi
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

4. Set up environment variables:
   ```bash
   # Create a .env file with:
   UPLOADTHING_API_KEY=your_api_key_here  # Get this from UploadThing dashboard
   ```

## Storage Configuration

We use UploadThing for video storage and delivery:

- Fast CDN delivery worldwide
- Reliable upload with retry mechanism
- Direct file URLs for easy integration
- Automatic video format handling

## Code Quality

We use ruff for code quality. Before submitting a PR, ensure your code:

1. Passes all ruff checks:
   ```bash
   ruff check .
   ```
2. Is properly formatted:
   ```bash
   ruff format .
   ```

### VSCode Integration

Install the ruff extension for VSCode for real-time linting and formatting.

## Testing

### Running Tests

Run all tests:

```bash
pytest
```

Run specific test categories:

```bash
# Run UploadThing integration tests
pytest tests/test_blob_storage.py::test_upload_file_to_uploadthing_real -v

# Run unit tests only
pytest tests/ -m "not integration"
```

### Writing Tests

1. Place tests in the `tests/` directory
2. Name test files with `test_` prefix
3. Name test functions with `test_` prefix
4. Use descriptive test names
5. Include both success and failure cases
6. Mock external services when appropriate

### Testing UploadThing Integration

When writing tests that involve UploadThing:

1. Use the provided mock fixtures for unit tests
2. Use `@pytest.mark.integration` for real API tests
3. Always clean up test files after upload
4. Test retry logic for network failures
5. Verify both `fileUrl` and `appUrl` handling

Example test structure:

```python
def test_upload_success(mock_video_file):
    """Test successful video upload."""
    # Test implementation

def test_upload_retry(mock_video_file):
    """Test retry logic on network failure."""
    # Test implementation

@pytest.mark.integration
def test_upload_real():
    """Test actual UploadThing integration."""
    # Real API test implementation
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Update tests and documentation
4. Run all tests and quality checks
5. Submit a PR with a clear description of changes

## Release Process

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create a release PR
4. After merge, tag the release

## Questions?

Feel free to open an issue for any questions about contributing.
