PROJECT_ID="hack-team-coding-ninjas"
REGION="us-central1"
IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/dockerimages/finai-mitra"
SERVICE_ACCOUNT="workload@hack-team-coding-ninjas.iam.gserviceaccount.com"
CLOUD_RUN_SERVICE="finai-mitra"

gcloud run deploy "$CLOUD_RUN_SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --service-account "$SERVICE_ACCOUNT" \
  --allow-unauthenticated \
  --port 8080
