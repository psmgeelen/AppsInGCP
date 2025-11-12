# Cloud Run Function Example

A Google Cloud Function (2nd gen) that processes Pub/Sub messages using Pandas for data transformation.

## Overview

This function receives JSON data through Pub/Sub, loads it into a Pandas DataFrame, performs transformations, and logs the results. It demonstrates a serverless data processing pipeline on Google Cloud Platform.

## Development

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Google Cloud SDK (for deployment)

### Setup

Install dependencies:

```bash
uv sync
```

### Local Testing

Run the function locally using the Functions Framework:

```shell script
uv run functions-framework --target process_pubsub_event --debug
```


This starts a local server on `http://localhost:8080` that mimics the Cloud Functions environment with debug logging enabled.

### Sending Test Requests

Use the provided `request.sh` script to send a test Pub/Sub event:

```shell script
chmod +x request.sh
./request.sh
```


This sends a CloudEvents-formatted request with a base64-encoded JSON payload containing sample records.

**Example payload structure:**
```json
{
  "records": [
    {"id": 1, "value": 10},
    {"id": 2, "value": 20}
  ]
}
```


The function will:
1. Decode the base64 message
2. Parse the JSON
3. Load records into a Pandas DataFrame
4. Add a `value_squared` column
5. Log the results

## Deployment

### Configuration

Edit `deploy.sh` to set your GCP configuration:

- `PROJECT_ID`: Your GCP project ID
- `REGION`: Deployment region (default: `europe-west3`)
- `TOPIC_NAME`: Pub/Sub topic that triggers the function

### Deploy to Google Cloud

Make the deploy script executable and run it:

```shell script
chmod +x deploy.sh
./deploy.sh
```


The deployment script will:
1. Export dependencies to `requirements.txt`
2. Copy necessary files to a temporary directory
3. Deploy the function to Cloud Run Functions (2nd gen)
4. Clean up temporary files

### Trigger the Deployed Function

Publish a message to your Pub/Sub topic:

```shell script
gcloud pubsub topics publish my-topic \
  --message='{"records": [{"id": 1, "value": 10}, {"id": 2, "value": 20}]}'
```


View logs:

```shell script
gcloud functions logs read process_pubsub_event --region=europe-west3
```


## Project Structure

```
CloudRunFunctionExample/
├── main.py           # Function implementation
├── pyproject.toml    # Project dependencies (uv format)
├── uv.lock          # Locked dependencies
├── deploy.sh        # Deployment script
├── request.sh       # Local testing helper
└── README.md        # This file
```


## Dependencies

- `functions-framework`: Local development and Cloud Functions runtime
- `pandas`: Data processing and transformation

## Notes

- The function uses Python 3.13 runtime
- Memory allocation: 512MB
- Timeout: 60 seconds
- Trigger: Cloud Pub/Sub topic
```
This README provides a complete guide for development, local testing with the `functions-framework` command you mentioned, and deployment to Google Cloud Platform.
```
