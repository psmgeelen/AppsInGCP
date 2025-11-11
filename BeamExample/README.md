# Apache Beam Pub/Sub Event Aggregation Pipeline

A production-ready Apache Beam pipeline that consumes events from Google Cloud Pub/Sub, aggregates them by counting and grouping event types within time windows.

## 🏗️ Architecture Overview

This pipeline demonstrates event-driven data processing using:

- **Input**: Google Cloud Pub/Sub subscription (Eventarc events)
- **Processing**: Apache Beam with windowed aggregations
- **Output**: Pub/Sub topic or console output
- **Runners**: DirectRunner (local) or DataflowRunner (GCP)
```

┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Pub/Sub    │────▶│  Beam        │────▶│  Pub/Sub    │
│  Input      │     │  Pipeline    │     │  Output     │
│ Subscription│     │  (Count &    │     │  Topic      │
│             │     │   Group)     │     │  (Optional) │
└─────────────┘     └──────────────┘     └─────────────┘
```
## ✨ Features

- **Pub/Sub Integration**: Reads from subscriptions, writes to topics
- **Event Parsing**: JSON message parsing with error handling
- **Windowed Aggregation**: Fixed time windows for event grouping
- **Event Counting**: Counts events by type/category
- **Flexible Output**: Console output or Pub/Sub topic
- **Production Ready**: Runs on Google Cloud Dataflow

## 📋 Prerequisites

### Local Development
- Python 3.7+
- Google Cloud SDK
- Apache Beam SDK

### GCP Requirements
- Google Cloud Project with billing enabled
- Pub/Sub API enabled
- Dataflow API enabled (for cloud execution)
- Service account with appropriate permissions

## 🚀 Installation

### Install Dependencies
```bash
cd BeamExample/app
pip install apache-beam[gcp]
```
Or using the project's pyproject.toml:
```bash
pip install -e .
```
## 🔧 GCP Setup

### 1. Enable Required APIs
```bash
# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable \
  pubsub.googleapis.com \
  dataflow.googleapis.com \
  storage.googleapis.com
```
### 2. Create Pub/Sub Resources
```bash
# Create input topic and subscription
gcloud pubsub topics create beam-input-events
gcloud pubsub subscriptions create beam-input-sub \
  --topic beam-input-events

# Create output topic (optional)
gcloud pubsub topics create beam-output-results
```
### 3. Create GCS Bucket for Dataflow
```bash
# Create bucket for staging and temp files
gsutil mb -p $PROJECT_ID -l us-central1 gs://${PROJECT_ID}-beam-dataflow
```
### 4. Set Up Service Account (Optional but Recommended)
```
bash
# Create service account
gcloud iam service-accounts create beam-pipeline-sa \
  --display-name "Beam Pipeline Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:beam-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/dataflow.worker

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:beam-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/pubsub.subscriber

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:beam-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/pubsub.publisher

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:beam-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/storage.objectAdmin
```
## 🏃 Running the Pipeline

### Local Execution (DirectRunner)

For development and testing:
```bash
python main.py \
  --input_subscription projects/${PROJECT_ID}/subscriptions/beam-input-sub \
  --window_size 60 \
  --runner DirectRunner
```
### GCP Dataflow Execution

For production workloads:
```bash
python main.py \
  --input_subscription projects/${PROJECT_ID}/subscriptions/beam-input-sub \
  --output_topic projects/${PROJECT_ID}/topics/beam-output-results \
  --window_size 60 \
  --runner DataflowRunner \
  --project ${PROJECT_ID} \
  --region us-central1 \
  --temp_location gs://${PROJECT_ID}-beam-dataflow/temp \
  --staging_location gs://${PROJECT_ID}-beam-dataflow/staging \
  --service_account_email beam-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com
```
### Additional Dataflow Options
```bash
# With autoscaling
python main.py \
  --input_subscription projects/${PROJECT_ID}/subscriptions/beam-input-sub \
  --output_topic projects/${PROJECT_ID}/topics/beam-output-results \
  --runner DataflowRunner \
  --project ${PROJECT_ID} \
  --region us-central1 \
  --temp_location gs://${PROJECT_ID}-beam-dataflow/temp \
  --staging_location gs://${PROJECT_ID}-beam-dataflow/staging \
  --num_workers 2 \
  --max_num_workers 10 \
  --autoscaling_algorithm THROUGHPUT_BASED \
  --worker_machine_type n1-standard-2
```
## 📊 Rendering/Visualizing the Pipeline

### 1. Generate Pipeline Graph (Local)

You can visualize the pipeline structure before execution:
```bash
# Install graphviz
pip install graphviz

# Render to DOT format
python main.py \
  --input_subscription projects/${PROJECT_ID}/subscriptions/beam-input-sub \
  --runner DirectRunner \
  --render_to pipeline_graph.dot

# Convert to PNG (requires graphviz installed)
dot -Tpng pipeline_graph.dot -o pipeline_graph.png
```
### 2. View in Dataflow UI

When running on Dataflow, you can view the pipeline graph in the GCP Console:
```bash
# Get the Dataflow job ID after launching
python main.py \
  --input_subscription projects/${PROJECT_ID}/subscriptions/beam-input-sub \
  --runner DataflowRunner \
  --project ${PROJECT_ID} \
  --region us-central1 \
  --temp_location gs://${PROJECT_ID}-beam-dataflow/temp \
  --staging_location gs://${PROJECT_ID}-beam-dataflow/staging

# Open in browser
echo "View at: https://console.cloud.google.com/dataflow/jobs/${REGION}/${JOB_ID}?project=${PROJECT_ID}"
```
The Dataflow UI provides:
- Real-time pipeline graph visualization
- Step-by-step execution metrics
- Throughput and latency statistics
- Worker logs and diagnostics

### 3. Interactive Beam Notebook (Optional)

For interactive development and visualization:
```python
import apache_beam as beam
from apache_beam.runners.interactive.interactive_runner import InteractiveRunner
import apache_beam.runners.interactive.interactive_beam as ib

# Create pipeline
p = beam.Pipeline(InteractiveRunner())

# ... define your pipeline ...

# Render and show
ib.show_graph(p)
```
## 📝 Configuration Options

### Command-Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `--input_subscription` | Pub/Sub subscription path | Yes | - |
| `--output_topic` | Pub/Sub output topic path | No | - |
| `--window_size` | Window size in seconds | No | 60 |
| `--runner` | Pipeline runner (DirectRunner or DataflowRunner) | No | DirectRunner |
| `--project` | GCP project ID | For Dataflow | - |
| `--region` | GCP region | For Dataflow | - |
| `--temp_location` | GCS temp location | For Dataflow | - |
| `--staging_location` | GCS staging location | For Dataflow | - |

## 🧪 Testing with Sample Events

### Publish Test Events
```bash
# Single event
gcloud pubsub topics publish beam-input-events \
  --message '{"type":"user_login","source":"web","timestamp":"2025-01-01T10:00:00Z"}'

# Multiple events
for i in {1..10}; do
  gcloud pubsub topics publish beam-input-events \
    --message "{\"type\":\"page_view\",\"source\":\"mobile\",\"id\":$i}"
done
```
### Python Test Script
```python
from google.cloud import pubsub_v1
import json

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('your-project-id', 'beam-input-events')

events = [
    {"type": "user_login", "source": "web"},
    {"type": "user_logout", "source": "web"},
    {"type": "page_view", "source": "mobile"},
    {"type": "user_login", "source": "mobile"},
]

for event in events * 100:  # Publish 400 events
    data = json.dumps(event).encode('utf-8')
    publisher.publish(topic_path, data)

print("Published test events")
```
## 📊 Expected Output

### Console Output Format
```json
{"event_type": "user_login", "count": 42}
{"event_type": "page_view", "count": 158}
{"event_type": "user_logout", "count": 35}
```
### Pub/Sub Output Format

Messages published to the output topic will have the same JSON format.

## 🔍 Monitoring and Debugging

### View Dataflow Job Logs
```bash
# List jobs
gcloud dataflow jobs list --region us-central1

# View job details
gcloud dataflow jobs describe JOB_ID --region us-central1

# Stream logs
gcloud dataflow jobs logs JOB_ID --region us-central1
```
### Monitor Pub/Sub Metrics
```bash
# Check subscription backlog
gcloud pubsub subscriptions describe beam-input-sub \
  --format="value(messageRetentionDuration,numUndeliveredMessages)"
```
## 🎯 Customization

### Modify Event Parsing

Edit the `ParsePubSubMessage` class in `main.py` to change how events are parsed:
```
python
class ParsePubSubMessage(beam.DoFn):
    def process(self, element):
        message_data = element.decode('utf-8')
        event = json.loads(message_data)
        
        # Customize grouping key
        key = f"{event.get('type')}_{event.get('source')}"
        yield (key, 1)
```
### Change Window Type

Replace `FixedWindows` with other window types:

```python
# Sliding windows
beam.window.SlidingWindows(60, 30)  # 60s windows, 30s slide

# Session windows
beam.window.Sessions(600)  # 10 minute gap

# Global window
beam.window.GlobalWindows()
```
```


## 🧹 Cleanup

```shell script
# Delete Pub/Sub resources
gcloud pubsub subscriptions delete beam-input-sub
gcloud pubsub topics delete beam-input-events
gcloud pubsub topics delete beam-output-results

# Delete GCS bucket
gsutil -m rm -r gs://${PROJECT_ID}-beam-dataflow

# Delete service account
gcloud iam service-accounts delete \
  beam-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com
```


## 📚 Additional Resources

- [Apache Beam Documentation](https://beam.apache.org/documentation/)
- [Google Cloud Dataflow Documentation](https://cloud.google.com/dataflow/docs)
- [Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Beam Programming Guide](https://beam.apache.org/documentation/programming-guide/)
- [Dataflow Pricing Calculator](https://cloud.google.com/products/calculator)

## 🤝 Support

For issues or questions:
- Apache Beam: [Stack Overflow](https://stackoverflow.com/questions/tagged/apache-beam)
- Google Cloud: [Support Portal](https://cloud.google.com/support)

## 📄 License

[Add your license information here]
```
This README provides comprehensive documentation including:
- Full GCP setup instructions with all necessary commands
- Multiple ways to run the pipeline (local and cloud)
- Detailed rendering/visualization options including the Dataflow UI
- Test data generation examples
- Monitoring and debugging guidance
- Customization examples
- Cleanup instructions
```
