# Dagster on GKE
Consider this a PoC that looks at running Dagster locally for development and in GKE for production.

## Local environment
Authentication with the GCP project happens through a service account. The commands below will create a service account and download a JSON key. This service account will also be used via Workload Identity when deployed in production on GKE.

```sh
gcloud config set project $GOOGLE_CLOUD_PROJECT;
gcloud iam service-accounts create dagster \
  --display-name="dagster";

export SA_EMAIL=`gcloud iam service-accounts list --format='value(email)' \
  --filter='displayName:dagster'`

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member serviceAccount:$SA_EMAIL \
  --role roles/bigquery.jobUser;

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member serviceAccount:$SA_EMAIL \
  --role roles/bigquery.user;

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member serviceAccount:$SA_EMAIL \
  --role roles/bigquery.dataEditor;

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member serviceAccount:$SA_EMAIL \
  --role roles/storage.admin;

gcloud iam service-accounts keys create service.json \
    --iam-account=$SA_EMAIL;
```

Complete your .env file.

```sh
poetry env use 3.9.10;
poetry install;
dagit -w dagster/workspace.yaml;
```


## Production
```sh
gcloud config set project $GOOGLE_CLOUD_PROJECT;
gcloud config set compute/region us-central1;

gcloud services enable artifactregistry.googleapis.com;
gcloud services enable cloudbuild.googleapis.com;
gcloud services enable compute.googleapis.com;
gcloud services enable container.googleapis.com;
gcloud services enable servicenetworking.googleapis.com;
gcloud services enable sqladmin.googleapis.com;
gcloud services enable iamcredentials.googleapis.com;
```

The production job uses the Google Cloud Storage (GCS) IO manager. This requires a GCS bucket.
```sh
gsutil mb gs://$GOOGLE_CLOUD_PROJECT
```

While the Dagster helm chart deploys PostgreSQL in the cluster, this deployment will connect to a Cloud SQL instance via a private ip.
```sh
gcloud compute addresses create google-managed-services-default \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=16 \
    --description="peering range" \
    --network=default;

gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges=google-managed-services-default \
    --network=default \
    --project=$GOOGLE_CLOUD_PROJECT;

# create cloud sql instance
gcloud beta sql instances create \
    --zone us-central1-c \
    --database-version POSTGRES_13 \
    --tier db-f1-micro \
    --storage-auto-increase \
    --network=projects/$GOOGLE_CLOUD_PROJECT/global/networks/default \
    --backup-start-time 08:00 dagster;

gcloud sql databases create 'dagster' --instance=dagster;

# TODO: set the postgres user password

# create artifact registry repository
gcloud artifacts repositories create dagster \
    --project=$GOOGLE_CLOUD_PROJECT \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository";

# create gke autopilot cluster
gcloud container clusters create-auto kubefun --region us-central1;

kubectl create secret generic dagster-gcs-bucket-name --from-literal=GCS_BUCKET_NAME=main-form-349700;
kubectl create secret generic dagster-postgresql-secret --from-literal=postgresql-password='SecretPassword';

helm repo add dagster https://dagster-io.github.io/helm ;

helm repo update;

gcloud builds submit \
    --tag us-central1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/dagster/dagster .;

helm upgrade --install dagster dagster/dagster -f values.yaml;

kubectl create configmap dagster-lea-vars \
    --from-literal GCS_BUCKET_DEV='dagster-dev-bucket-name' \
    --from-literal GCS_BUCKET_PROD='dagster-prod-bucket-name' \
    --from-literal DBT_PROJECT_DIR='/opt/dagster/app/dbt' \
    --from-literal DBT_PROFILES_DIR='/opt/dagster/app';

kubectl create secret generic dagster-edfi-api \
    --from-literal EDFI_BASE_URL='XXXXXXXX' \
    --from-literal EDFI_API_KEY='XXXXXXXX' \
    --from-literal EDFI_API_SECRET='XXXXXXXX';

# bind kubernetes service account to google service account
gcloud iam service-accounts add-iam-policy-binding \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:$GOOGLE_CLOUD_PROJECT.svc.id.goog[default/dagster]" \
  dagster@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com;

kubectl annotate serviceaccount \
  default \
  iam.gke.io/gcp-service-account=dagster@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com;

kubectl annotate serviceaccount \
  dagster \
  iam.gke.io/gcp-service-account=dagster@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com;

export DAGIT_POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=dagster,app.kubernetes.io/instance=dagster,component=dagit" -o jsonpath="{.items[0].metadata.name}")

kubectl --namespace default port-forward $DAGIT_POD_NAME 8080:80;
```
