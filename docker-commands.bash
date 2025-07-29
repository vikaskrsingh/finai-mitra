gcloud auth configure-docker europe-docker.pkg.dev
docker buildx build --platform=linux/amd64 -t us-central1-docker.pkg.dev/hack-team-coding-ninjas/dockerimages/finai-mitra .
docker push us-central1-docker.pkg.dev/hack-team-coding-ninjas/dockerimages/finai-mitra




