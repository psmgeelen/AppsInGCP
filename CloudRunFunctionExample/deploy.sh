#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="your-gcp-project-id"
REGION="europe-west3"
FUNCTION_NAME="process_pubsub_event"
TOPIC_NAME="my-topic"
RUNTIME="python313"
ENTRY_POINT="process_pubsub_event"

# === Prepare temp deployment dir ===
TMP_DIR=$(mktemp -d)
echo "📦 Using temporary directory: $TMP_DIR"

# Copy main.py
cp main.py "$TMP_DIR/"

# Export dependencies from uv environment
echo "📦 Exporting requirements..."
uv export > "$TMP_DIR/requirements.txt"

# Optional: copy any other needed files (e.g., helper modules)
# cp -r my_module "$TMP_DIR/"

# === Deploy function from temp dir ===
echo "🚀 Deploying $FUNCTION_NAME..."
gcloud functions deploy "$FUNCTION_NAME" \
  --gen2 \
  --runtime "$RUNTIME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --trigger-topic "$TOPIC_NAME" \
  --entry-point "$ENTRY_POINT" \
  --source "$TMP_DIR" \
  --memory 512Mi \
  --timeout 60s

echo "✅ Deployment complete!"

# Clean up temp dir
rm -rf "$TMP_DIR"
echo "🧹 Temporary directory removed."
