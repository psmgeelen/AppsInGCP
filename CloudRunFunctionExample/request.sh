curl -X POST localhost:8080 \
  -H "Content-Type: application/cloudevents+json" \
  -d '{
    "specversion": "1.0",
    "id": "abc-123",
    "source": "//pubsub.googleapis.com/projects/demo/topics/test",
    "type": "google.cloud.pubsub.topic.v1.messagePublished",
    "data": {
      "message": {
        "data": "eyJyZWNvcmRzIjogW3siaWQiOiAxLCAidmFsdWUiOiAxMH0sIHsiaWQiOiAyLCAidmFsdWUiOiAyMH1dfQ=="
      }
    }
  }'
