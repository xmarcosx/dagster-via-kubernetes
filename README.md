## Dagster on GKE

```sh

gcloud services enable compute.googleapis.com;
gcloud services enable container.googleapis.com;

gcloud config set compute/region us-central1;

# create gke autopilot cluster
gcloud container clusters create-auto my-cluster;

# get auth credentials so kubectl can interact with the cluster
# gcloud container clusters get-credentials my-cluster;

helm repo add dagster https://dagster-io.github.io/helm;

helm repo update;

helm show values dagster/dagster > values.yaml;

helm upgrade --install dagster dagster/dagster -f values.yaml;

export DAGIT_POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=dagster,app.kubernetes.io/instance=dagster,component=dagit" -o jsonpath="{.items[0].metadata.name}");

kubectl --namespace default port-forward $DAGIT_POD_NAME 8080:80;

```
