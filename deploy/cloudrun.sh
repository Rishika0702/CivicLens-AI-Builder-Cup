#!/usr/bin/env bash
set -euo pipefail
: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
: "${GOOGLE_CLOUD_REGION:=asia-south1}"
gcloud config set project "$GOOGLE_CLOUD_PROJECT"
# Prerequisite: gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
# Create secret gemini-api-key and grant Cloud Run runtime service account secret accessor.
gcloud run deploy civiclens --source . --region "$GOOGLE_CLOUD_REGION" --allow-unauthenticated --set-env-vars=FIRESTORE_ENABLED=true,REQUIRE_AUTH=false --set-secrets=GEMINI_API_KEY=gemini-api-key:latest
