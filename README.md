## Dagster on GKE

### Local environment
Authentication with the GCP project happens through a service account. In GCP, head to _IAM & Admin --> Service Accounts_ to create your service account.

* Click **Create Service Account**
* Choose a name (ie. dagster) and click **Create**
* Grant the service account the following roles
    * BigQuery Job User
    * BigQuery User
    * BigQuery Data Editor
    * Storage Admin
* Click **Done** 
* Select the actions menu and click **Create key**. Create a JSON key, rename to _service.json_ and store in the root of the repository.


### Production

```sh

gsutil mb gs://cool-bucket-name

```

```sh
gcloud services enable artifactregistry.googleapis.com;
gcloud services enable cloudbuild.googleapis.com;
gcloud services enable compute.googleapis.com;
gcloud services enable container.googleapis.com;

gcloud config set compute/region us-central1;

# create artifact registry repository
gcloud artifacts repositories create dagster \
    --project=$GOOGLE_CLOUD_PROJECT \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository";

# create gke autopilot cluster
gcloud container clusters create-auto kubefun;

helm repo add dagster https://dagster-io.github.io/helm;

helm repo update;

gcloud builds submit \
    --tag us-central1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/dagster/dagster .;

helm upgrade --install dagster dagster/dagster --namespace dagster --create-namespace -f values.yaml;

export DAGIT_POD_NAME=$(kubectl get pods --namespace dagster -l "app.kubernetes.io/name=dagster,app.kubernetes.io/instance=dagster,component=dagit" -o jsonpath="{.items[0].metadata.name}")

kubectl --namespace dagster port-forward $DAGIT_POD_NAME 8080:80

```
