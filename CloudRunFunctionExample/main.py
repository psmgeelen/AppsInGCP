import functions_framework
import base64
import json
import pandas as pd

# Triggered by a Pub/Sub message
@functions_framework.cloud_event
def process_pubsub_event(cloud_event):
    # Decode Pub/Sub message data
    pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    print("Raw Pub/Sub message:", pubsub_message)

    # Parse JSON payload
    try:
        payload = json.loads(pubsub_message)
    except json.JSONDecodeError:
        print("Invalid JSON in message.")
        return

    # Example: assume payload contains a list of records
    # e.g. {"records": [{"id":1,"value":10},{"id":2,"value":20}]}
    if "records" not in payload:
        print("No 'records' key found in payload.")
        return

    # Load into pandas DataFrame
    df = pd.DataFrame(payload["records"])
    print("DataFrame loaded:")
    print(df)

    # Example processing: compute a new column
    df["value_squared"] = df["value"] ** 2
    print("Processed DataFrame:")
    print(df)

    # In a real function, you could write results to BigQuery, GCS, etc.
    # For now, just log the results
    print("Processing complete.")
