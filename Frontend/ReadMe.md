# Chainlit Chat Application for Google Cloud Platform

A production-ready Chainlit chat application with integrated user registration and authentication, designed for deployment on **Google Cloud Run**. This application demonstrates event-driven architecture using Google Cloud Pub/Sub and Firestore for state management.

## 🏗️ Architecture Overview

This application is a frontend service that integrates with backend processing services through an event-driven architecture:

- **Frontend**: Chainlit web interface with password authentication
- **State Management**: Google Cloud Firestore for user data, sessions, and chat history
- **Event Bus**: Google Cloud Pub/Sub for asynchronous message processing
- **Deployment Target**: Google Cloud Run (serverless container platform)
```

┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   User      │────▶│   Chainlit   │────▶│  Firestore  │
│  Browser    │◀────│   Frontend   │◀────│  Database   │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   Pub/Sub    │────▶│  Backend    │
                    │   Topics     │◀────│  Services   │
                    └──────────────┘     └─────────────┘
```
## ✨ Features

### Integrated User Registration & Authentication
- **No separate registration flow required** - users register automatically on first login
- Password-based authentication with SHA-256 hashing
- User credentials stored securely in Firestore
- Minimum password length validation (6 characters)
- Automatic user session management

### Event-Driven Communication
- **Context Requests**: Published to `ContextRequest` topic for session initialization
- **Chat Requests**: Published to `ChatRequest` topic for message processing
- Firestore-based response polling for async backend communication

### Session Management
- Persistent user sessions stored in Firestore
- Context loading and caching per user
- Chat history tracking with timestamps

## 🔧 Infrastructure Requirements

### Required GCP Services

1. **Cloud Run** (for hosting the application)
   - Minimum 512MB memory recommended
   - CPU: 1 vCPU minimum
   - Concurrency: 80 requests per container (default)

2. **Cloud Firestore** (Native mode)
   - Collections required:
     - `users` - User credentials and metadata
     - `sessions` - User session context
     - `chats` - Chat history and responses

3. **Cloud Pub/Sub**
   - Topics required:
     - `ContextRequest` - For session initialization events
     - `ChatRequest` - For chat message processing events
   - Subscriptions: Created by backend services consuming these topics

4. **Secret Manager** (recommended for production)
   - Store `CHAINLIT_AUTH_SECRET`
   - Store service account credentials if needed

5. **Artifact Registry** (for container images)
   - Repository to store Docker images

### IAM Permissions Required

The Cloud Run service account needs:
- `roles/datastore.user` - Firestore read/write access
- `roles/pubsub.publisher` - Pub/Sub publishing rights
- `roles/secretmanager.secretAccessor` - Access to secrets (if using Secret Manager)

## 🚀 Deployment to Google Cloud Run

### Prerequisites
```
bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```
### Step 1: Enable Required APIs
```
bash
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```
### Step 2: Create Firestore Database
```
bash
# Create Firestore database (if not exists)
gcloud firestore databases create --location=us-central1
```
### Step 3: Create Pub/Sub Topics
```
bash
# Create required topics
gcloud pubsub topics create ContextRequest
gcloud pubsub topics create ChatRequest
```
### Step 4: Create Secret for Authentication
```
bash
# Generate a secure random secret
openssl rand -base64 32

# Store it in Secret Manager
gcloud secrets create chainlit-auth-secret \
  --data-file=- <<< "YOUR_GENERATED_SECRET_HERE"
```
### Step 5: Build and Push Container Image
```
bash
# Navigate to Frontend directory
cd Frontend

# Set variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export SERVICE_NAME=chainlit-app
export IMAGE_NAME=gcr.io/$PROJECT_ID/$SERVICE_NAME

# Build the image
docker build -t $IMAGE_NAME .

# Push to Google Container Registry
docker push $IMAGE_NAME
```
Alternatively, use Cloud Build:
```
bash
gcloud builds submit --tag $IMAGE_NAME
```
### Step 6: Deploy to Cloud Run
```
bash
# Deploy the service
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID" \
  --set-env-vars "CONTEXT_REQUEST_TOPIC=ContextRequest" \
  --set-env-vars "CHAT_REQUEST_TOPIC=ChatRequest" \
  --set-env-vars "PYTHONUNBUFFERED=1" \
  --set-secrets "CHAINLIT_AUTH_SECRET=chainlit-auth-secret:latest"
```
### Step 7: Get the Service URL
```
bash
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)'
```
## 🔐 Environment Variables

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | `my-project-123456` |
| `CONTEXT_REQUEST_TOPIC` | Pub/Sub topic for context requests | `ContextRequest` |
| `CHAT_REQUEST_TOPIC` | Pub/Sub topic for chat messages | `ChatRequest` |
| `CHAINLIT_AUTH_SECRET` | Secret key for session encryption | `random-32-byte-string` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PUBSUB_EMULATOR_HOST` | Pub/Sub emulator (local dev) | _(none)_ |
| `FIRESTORE_EMULATOR_HOST` | Firestore emulator (local dev) | _(none)_ |
| `PYTHONUNBUFFERED` | Disable Python output buffering | `1` |

## 🧪 Local Development

### Using Docker Compose (Recommended)

The included `docker-compose.yaml` sets up local emulators for Pub/Sub and Firestore:
```
bash
# Start all services (app + emulators)
docker-compose up

# Access the app at http://localhost:8000
```
### Manual Setup
```
bash
# Create virtual environment
cd Frontend/app
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install uv
uv sync

# Start Firestore emulator (separate terminal)
gcloud beta emulators firestore start --host-port=localhost:8086

# Start Pub/Sub emulator (separate terminal)
gcloud beta emulators pubsub start --host-port=localhost:8085

# Set environment variables
export PUBSUB_EMULATOR_HOST=localhost:8085
export FIRESTORE_EMULATOR_HOST=localhost:8086
export GCP_PROJECT_ID=local-test-project
export CONTEXT_REQUEST_TOPIC=ContextRequest
export CHAT_REQUEST_TOPIC=ChatRequest
export CHAINLIT_AUTH_SECRET=dev-secret-key-change-in-production

# Run the application
chainlit run main.py
```
## 📝 User Registration Flow

1. **User visits the application** - Presented with login screen
2. **Enter new credentials** - Username + password (min 6 chars)
3. **Automatic registration** - If username doesn't exist, account is created
4. **Immediate login** - User is logged in and can start chatting
5. **Welcome message** - New users see registration confirmation

### For Existing Users
- Simply enter username and password
- No registration step needed

## 🔍 Firestore Data Structure

### Users Collection (`users`)
```
json
{
  "username": "john_doe",
  "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
  "created_at": "2025-01-15T10:30:00Z"
}
```
### Sessions Collection (`sessions`)
```
json
{
  "context": { /* user-specific context data */ },
  "ready": true,
  "updated_at": "2025-01-15T10:35:00Z"
}
```
### Chats Collection (`chats`)
```
json
{
  "username": "john_doe",
  "request": "What is the weather today?",
  "response": "The weather is sunny and 72°F",
  "status": "completed",
  "ready": true,
  "timestamp": "2025-01-15T10:36:00Z"
}
```
## 🔒 Security Considerations

### Production Recommendations

1. **Use Secret Manager** for sensitive credentials
2. **Enable Cloud Run Authentication** if you want Google-based access control
3. **Use stronger password hashing** - Consider bcrypt or Argon2 instead of SHA-256
4. **Implement rate limiting** to prevent brute force attacks
5. **Add password complexity rules** (uppercase, numbers, special chars)
6. **Enable Cloud Armor** for DDoS protection
7. **Set up monitoring and alerting** with Cloud Monitoring
8. **Regular security audits** of Firestore rules and IAM permissions

### Firestore Security Rules Example
```
javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only read/write their own documents
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    match /sessions/{sessionId} {
      allow read, write: if request.auth != null && request.auth.uid == sessionId;
    }
    
    match /chats/{chatId} {
      allow read, write: if request.auth != null;
    }
  }
}
```
## 📊 Monitoring and Logging

### Cloud Run Logs
```
bash
# View logs
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --limit 50

# Stream logs
gcloud run services logs tail $SERVICE_NAME \
  --region $REGION
```
### Metrics to Monitor

- Request count and latency
- Error rate (4xx, 5xx responses)
- Container instance count
- Memory and CPU utilization
- Pub/Sub publish success/failure rate
- Firestore read/write operations

## 🧹 Cleanup
```
bash
# Delete Cloud Run service
gcloud run services delete $SERVICE_NAME --region $REGION

# Delete Pub/Sub topics
gcloud pubsub topics delete ContextRequest
gcloud pubsub topics delete ChatRequest

# Delete container images
gcloud container images delete $IMAGE_NAME

# Delete secrets
gcloud secrets delete chainlit-auth-secret
```
## 📚 Additional Resources

- [Chainlit Documentation](https://docs.chainlit.io/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)

## 🤝 Support

For issues or questions, please refer to the project repository or Google Cloud support channels.

## 📄 License

[Add your license information here]
```


This comprehensive README provides everything needed to understand, deploy, and maintain the application on Google Cloud Platform!