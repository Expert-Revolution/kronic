<p align="center">
    <img src="./static/android-chrome-192x192.png" alt="icon">
</p>

# Kronic

![Build / Test](https://github.com/mshade/kronic/actions/workflows/build.yaml/badge.svg)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

The simple Kubernetes CronJob admin UI.

Kronic is in early alpha. It may eat your cronjobs, pods, or even your job.
Avoid exposing Kronic to untrusted parties or networks or using Kronic near anything even vaguely important.


## Screenshots

See CronJobs across namespaces:
![Homepage](/.github/kronic-home.png)

View, suspend, trigger, clone, or delete CrobJobs at a glance:
![Cronjobs in a Namespace](/.github/kronic-namespace.png)

Drill down into details to see the status of jobs and pods:
![Cronjob Detail view](/.github/kronic-detail.png)

Get your hands dirty with the raw YAML to edit a CronJob:
![Cronjob Edit view](/.github/kronic-edit.png)


## Purpose

CronJobs are a powerful tool, but I have found that developers and stakeholders often need an easy way to inspect the status of jobs,
trigger them ad-hoc, or create a new one-off job based on existing CronJob definitions.

Kronic aims to be a simple admin UI / dashboard / manager to view, suspend, trigger, edit, and delete CronJobs in a Kubernetes cluster.


## Configuration

Kronic can be limited to a list of namespaces. Specify as a comma separated list in the `KRONIC_ALLOW_NAMESPACES` environment variable.
The helm chart exposes this option.

Kronic also supports a namespaced installation. The `KRONIC_NAMESPACE_ONLY`
environment variable will limit Kronic to interacting only with CronJobs, Jobs
and Pods in its own namespace. Enabling this setting in the helm chart values
(`env.KRONIC_NAMESPACE_ONLY="true"`) will prevent creation of ClusterRole and
ClusterRolebinding, creating only a namespaced Role and RoleBinding.

### Network Policy

The helm chart provides a NetworkPolicy resource that can be enabled to control traffic to the Kronic pods. 
By default, the NetworkPolicy is disabled. It can be enabled by setting `networkPolicy.enabled=true` in your values file:

```yaml
networkPolicy:
  enabled: true                  # Enable NetworkPolicy
  namespaceSelector: {}          # Configure namespaceSelector for ingress
  podSelector: {}                # Configure podSelector for ingress
  additionalIngress: []          # Additional ingress rules
```

### Authentication

Kronic supports HTTP Basic authentication to the backend. It is enabled by default when installed via the helm chart. If no password is specified, the default username is `kronic` and the password is generated randomly.
A username and password can be set via helm values under `auth.adminUsername` and `auth.adminPassword`, or you may create a Kubernetes secret for the deployment to reference.

To retrieve the randomly generated admin password:
```
kubectl --namespace <namespace> get secret <release-name> -ojsonpath="{.data.password}" | base64 -d
```

To create an admin password secret for use with Kronic:
```
kubectl --namespace <namespace> create secret generic custom-password --from-literal=password=<password>

## Tell the helm chart to use this secret:
helm --namespace <namespace> upgrade kronic kronic/kronic --set auth.existingSecretName=custom-password
```

## Deploying to K8S

A helm chart is available at [./chart/kronic](./chart/kronic/). 
By default the Kronic helm chart will provide only a `ClusterIP` service. See the [values.yaml](./chart/kronic/values.yaml) for settings,
most notably the `ingress` section. 

> **Warning**
> Avoid exposing Kronic publicly! The default configuration allows for basic authentication, but
> provides only minimal protection. 

To install Kronic as `kronic` in its own namespace:

```
helm repo add kronic https://mshade.github.io/kronic/
helm repo update

# Optionally fetch, then customize values file
helm show values kronic/kronic > myvalues.yaml

helm install -n kronic --create-namespace kronic kronic/kronic

# See the NOTES output for accessing Kronic and retrieving the initial admin password
```

If no ingress is configured (see warning above!), expose Kronic via `kubectl port-forward` and access `localhost:8000` in your browser:

```
kubectl -n kronic port-forward deployment/kronic 8000:8000
```

## Running Locally

### Automated Local Development (Recommended)

For a complete local development environment with automated k3d cluster provisioning:

**Prerequisites:**
- Docker
- [k3d](https://k3d.io/) - Lightweight Kubernetes in Docker

**Quick Start:**
```bash
# Start complete development environment
./scripts/dev.sh up

# Access Kronic at http://localhost:5000
# Default credentials: admin / test2
```

**Available Commands:**
```bash
./scripts/dev.sh up       # Start k3d cluster and Kronic
./scripts/dev.sh down     # Stop and clean up everything
./scripts/dev.sh restart  # Restart the environment
./scripts/dev.sh status   # Check status of services
./scripts/dev.sh logs     # View Kronic logs
```

The development script automatically:
- Creates a k3d cluster named `kronic-localdev`
- Configures networking for container communication  
- Builds and starts Kronic with docker-compose
- Sets up proper kubeconfig mounting and permissions

### Manual Local Deployment

If you prefer to run against an existing cluster, Kronic can use any `KUBECONFIG` file:

```
docker run -i --name kronic \
    -v $HOME/.kube:/home/kronic/.kube \
    -p 8000:8000 \
    ghcr.io/mshade/kronic
```

> **Note**
> You may need to ensure permissions on the kubeconfig file are readable to the `kronic` user (uid 3000). You may also mount a specific kubeconfig file into place, ie: `-v $HOME/.kube/kronic.yaml:/home/kronic/.kube/config`


## Design

Kronic is a small Flask app built with:
- the Python Kubernetes client
- gunicorn
- [AlpineJS](https://alpinejs.dev/)
- [PicoCSS](https://picocss.com/)


## Development and Testing

### Running Tests

Kronic has both unit tests and integration tests:

**Unit Tests** (fast, no external dependencies):
```bash
pytest tests/ -m "not integration"
```

**Integration Tests** (slower, requires Docker and kind):
```bash
pytest tests/ -m "integration"
```

**All Tests**:
```bash
pytest tests/
```

The integration tests automatically create and manage ephemeral Kubernetes clusters using [kind](https://kind.sigs.k8s.io/) to test Kronic's functionality against real Kubernetes resources. They require:
- Docker
- kubectl 
- kind (automatically installed if not present)

Integration tests are automatically skipped if the required tools are not available.


## Todo

- [x] CI/CD pipeline and versioning
- [x] Helm chart
- [x] Allow/Deny lists for namespaces
- [x] Support a namespaced install (no cluster-wide view)
- [x] Built-in auth option
- [x] Integration tests against ephemeral Kubernetes cluster
- [ ] Display elements and handling for `spec.timezone`
- [x] NetworkPolicy in helm chart
- [ ] Timeline / Cron schedule interpreter or display
- [ ] YAML/Spec Validation on Edit page
- [ ] Async refreshing of job/pods
- [ ] Error handling for js apiClient
- [ ] Better logging from Flask app and Kron module
- [ ] Improve test coverage
- [x] Improve localdev stack with automated k3d cluster provisioning
