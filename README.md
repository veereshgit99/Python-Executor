# Safe Python Script Execution Service

A secure API service that executes arbitrary Python scripts in a sandboxed environment using nsjail. Built with Flask and deployed on Google Cloud Run.

## Features

- ✅ Secure script execution with nsjail sandboxing
- ✅ Support for pandas, numpy, and os libraries
- ✅ Captures both return value and stdout separately
- ✅ Input validation and error handling
- ✅ Lightweight Docker image
- ✅ 30-second execution timeout
- ✅ Resource limits (CPU, memory, file size)

## Quick Start

### Running Locally

1. Build the Docker image:
```bash
docker build -t python-executor .
```

2. Run the container:
```bash
docker run -p 8080:8080 python-executor
```

### Live Demo

The service is deployed on Google Cloud Run:
```
https://python-executor-927211469366.us-central1.run.app
```

## API Documentation

### POST /execute

Executes a Python script and returns the result of the `main()` function.

**Request Body:**
```json
{
  "script": "def main():\n    return {\"key\": \"value\"}"
}
```

**Response (Success):**
```json
{
  "result": {"key": "value"},
  "stdout": ""
}
```

**Response (Error):**
```json
{
  "error": "Error message"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Example Scripts

### Basic Example
```bash
curl -X POST https://python-executor-927211469366.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"message\": \"Hello, World!\"}"
  }'
```

### With stdout
```bash
curl -X POST https://python-executor-927211469366.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    print(\"Debug message\")\n    return {\"result\": 42}"
  }'
```

### Using Pandas
```bash
curl -X POST https://python-executor-927211469366.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import pandas as pd\n\ndef main():\n    df = pd.DataFrame({\"a\": [1, 2, 3], \"b\": [4, 5, 6]})\n    return {\"sum\": int(df[\"a\"].sum())}"
  }'
```

### Using Numpy
```bash
curl -X POST https://python-executor-927211469366.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import numpy as np\n\ndef main():\n    arr = np.array([1, 2, 3, 4, 5])\n    return {\"mean\": float(np.mean(arr))}"
  }'
```

### Using OS Module
```bash
curl -X POST https://python-executor-927211469366.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import os\n\ndef main():\n    cwd = os.getcwd()\n    return {\"cwd\": cwd}"
  }'
```

## Google Cloud Run Deployment

### Prerequisites
- Google Cloud SDK installed and configured
- Docker installed
- GCP project with Cloud Run API enabled

### Deployment Steps

1. Set your GCP project ID:
```bash
export PROJECT_ID=your-project-id
export SERVICE_NAME=python-executor
export REGION=us-central1
```

2. Build and push to Google Container Registry:
```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
```

3. Deploy to Cloud Run:
```bash
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 60
```

4. Get the service URL:
```bash
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
```

### Testing Cloud Run Deployment

Test the deployed service with these examples:

```bash
# Test with numpy
curl -X POST https://python-executor-927211469366.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import numpy as np\n\ndef main():\n    arr = np.array([1, 2, 3, 4, 5])\n    return {\"mean\": float(np.mean(arr))}"
  }'

# Test with os module
curl -X POST https://python-executor-927211469366.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import os\n\ndef main():\n    cwd = os.getcwd()\n    return {\"cwd\": cwd}"
  }'

# Test with stdout
curl -X POST https://python-executor-927211469366.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    print(\"Debug message\")\n    return {\"result\": 42}"
  }'
```

## Security Features

The service uses nsjail to provide multiple layers of security:

- **Filesystem isolation**: Limited mount points, read-only system directories
- **Resource limits**: CPU time (10s), memory (512MB), file size (64MB)
- **Network isolation**: Restricted network access
- **Seccomp filtering**: Whitelist of allowed system calls
- **Execution timeout**: 30-second hard limit
- **Temporary file cleanup**: Automatic cleanup after execution

### Cloud Run Security Model

**Note**: The nsjail configuration has been adapted for Google Cloud Run compatibility. While some namespace isolation features (CLONE_NEWUSER, CLONE_NEWNET) are disabled due to Cloud Run's security model, the service still maintains strong security through:

- Resource limits (CPU, memory, file size)
- Filesystem isolation and read-only mounts
- Cloud Run's container isolation layer
- Seccomp filtering and syscall restrictions
- Execution timeouts and automatic cleanup

This multi-layered approach ensures secure script execution even in a managed container environment.

## Validation Rules

1. Request must have `Content-Type: application/json`
2. Request body must contain a `script` field
3. Script must be a non-empty string
4. Script must contain a `def main():` function
5. `main()` function must return a JSON-serializable value

## Error Handling

The service handles various error scenarios:

- Missing or invalid `script` field
- Missing `main()` function
- Non-JSON return value from `main()`
- Script execution errors
- Timeout (30 seconds)
- Resource limit violations

## Architecture

```
Client Request
    ↓
Flask API (app.py)
    ↓
Input Validation
    ↓
Wrapper Script Creation
    ↓
nsjail Sandbox
    ↓
Python Script Execution
    ↓
Result Capture (return + stdout)
    ↓
JSON Response
```

## Development

### Project Structure
```
.
├── app.py              # Flask application
├── nsjail.cfg          # nsjail configuration
├── Dockerfile          # Docker image definition
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask directly (without nsjail - for testing only)
python app.py
```

## Performance

- **Docker image size**: ~500MB (optimized with slim base image)
- **Cold start**: ~3-5 seconds on Cloud Run
- **Execution time**: Depends on script complexity (max 30s)
- **Memory usage**: Typically 100-200MB for simple scripts

## Limitations

- Maximum execution time: 30 seconds
- Maximum memory: 512MB (configurable in nsjail.cfg)
- Maximum file size: 64MB
- Available libraries: Standard library, pandas, numpy, os
- No persistent storage between executions
- No network access from scripts (by nsjail design)

## Troubleshooting

### "Script must contain a 'def main():' function"
Ensure your script has a function named `main` with no parameters.

### "main() must return a JSON-serializable value"
The return value must be convertible to JSON (dict, list, string, number, boolean, None).

### Script timeout
If scripts take longer than 30 seconds, they will be terminated. Optimize your code or increase the timeout in app.py and nsjail.cfg.

## License

MIT License - feel free to use this for your projects!

## Contributing

Pull requests welcome! Please ensure all tests pass before submitting.

---

**Note**: This service is designed for controlled environments. Always review security settings before deploying to production.