# gae-init

[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg)](https://github.com/prettier/prettier)

> **gae-init** is the easiest boilerplate to kick start new applications on Google App Engine using Python, Flask, RESTful, Bootstrap and tons of other cool features.

Read the [documentation][], where you can find a complete [feature list][], a detailed [tutorial][], the [how to][] section and more..

## Requirements

- [Google App Engine (GAE) Standard SDK for Python 3][google app engine]
- [uv][] [rust-just][] [Node.js][], [Yarn][], [uv][]
- [Linux][] or [macOS][] or [Windows][]

### Install the Requirements

Confirm that you have a supported version of Python and the Google Cloud CLI installed:

```bash
# expecting Python 3.12.3 or newer
python --version

# expecting Google Cloud CLI (aka gcloud) installed
# (core and beta 2026.10.09 or newer, Google Cloud SDK 589.0.0 or newer)
gcloud -v
```

The following applies to [Linux][] (adjust accordingingly for other platforms):

```bash
# add specific components
gcloud components install app-engine-python app-engine-python-extras \
    cloud-datastore-emulator cloud-firestore-emulator

# download and install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# download and install Node.js
fnm install 24 && fnm default 24 && fnm use 24
# expecting Node.js v24.15.0 or newer
node -v

# update npm to specific version
npm install -g npm@12.0.2
# expecting npm 12.0.2 or newer
npm -v

# install Yarn
npm install --global yarn@1
# expecting yarn 1.22.22 or newer
yarn -v
```

## Initializing the project

```bash
cd /path/to/project-name
just install
just build-dev
```

## Running the Development Environment

Start the local datastore emulator in one terminal/console:

```bash
cd /path/to/project-name
just ds-start
# to start a new empty datastore:
#  just ds-start new
# to import from a GAE datastore export:
#  just ds-start ./datastore-snapshot/
```

Then start the local development server in another terminal/console:

```bash
cd /path/to/project-name
just dev
```

To test it visit `http://127.0.0.1:8080/` in your browser.

To stop the local datastore emulator:

```bash
just ds-stop
```

This will also export/save the current datastore state.

---

For a complete list of commands:

```bash
just --list
```

## Deploying on Google App Engine

```bash
just build-min
just export-reqs
just deploy
```

## Resetting the project

If something goes wrong you can always do:

```bash
just clean-all
just install
just build-dev
```

## Connecting the App to Memorystore for Redis

The original `gae-init` on Google App Engine (GAE) Standard Python 2 could use the built-in Memcache for Level 2 (L2) cache for NDB, which made it extremely useful and fast. However, in GAE Standard Python 3 this is no longer an option for the NDB portion. There is some Memcache support with the `app_engine_apis: true` setting, though that is not available for NDB anymore.

While `gae-in` can run without L2 cache for NDB (it will just be a little slower and produce more read operations), the replacement is using Memorystore for Redis. Unfortunately that is always a paid option. Below instructions configure a `basic` Redis, which is the cheapest option, and utilize the preview Direct VPC Egress approach. Using that Direct VPC Egress, there is no need for a dedicated (and always paid) VPC Connector (aka Serverless VPC Access Connector, typically created with at least 2 `e2-micro` instances).

Setting up Memorystore for Redis securely requires routing App Engine traffic through a dedicated Virtual Private Cloud (VPC) network rather than the GCP `default` network. Using the Direct VPC Egress approach, your GAE Standard Python 3 instances will be able to utilize the Redis server over the VPC network; without exposing the Redis server to the rest of the world.

### 1. Environment & API Setup

```bash
# Check App Engine location to verify region alignment
gcloud app describe --format="value(locationId)"

# Set configuration variables:
export PROJECT_ID=$(gcloud config get-value project)
export REGION=$(gcloud config get-value compute/region 2>/dev/null || echo "us-central1")
export ZONE="${REGION}-a"

# Check whether these fit your purpose:
echo -e "Using (please check or override):" \
    "\n\tPROJECT_ID=${PROJECT_ID}\n\tREGION=${REGION}\n\tZONE=${ZONE}"

# obtain the Project Number and Service Agent
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
export GAE_SERVICE_AGENT=$(gcloud projects get-iam-policy ${PROJECT_ID} \
        --flatten="bindings[].members" \
        --filter="bindings.role:roles/appengine.serviceAgent" \
        --format="value(bindings.members)" | head -n 1 | sed 's/^serviceAccount://')

# Override/correct as needed, then continue with:
export VPC_NAME="${PROJECT_ID}-vpc"
export REDIS_INSTANCE="${PROJECT_ID}-redis-instance"
export APPENGINE_SUBNET="${PROJECT_ID}-appengine-subnet"
export BASTION_NAME="${PROJECT_ID}-bastion"
export BASTION_SUBNET="${PROJECT_ID}-bastion-subnet"

echo -e "Using (please check or override):" \
    "\n\tPROJECT_ID=${PROJECT_ID}\n\tREGION=${REGION}\n\tZONE=${ZONE}  <-- Check" \
    "\n\tPROJECT_NUMBER=${PROJECT_NUMBER}\n\tGAE_SERVICE_AGENT=${GAE_SERVICE_AGENT}" \
    "\n\t-------------------------" \
    "\n\tVPC_NAME=${VPC_NAME}" \
    "\n\tREDIS_INSTANCE=${REDIS_INSTANCE}" \
    "\n\tAPPENGINE_SUBNET=${APPENGINE_SUBNET}" \
    "\n\tBASTION_NAME=${BASTION_NAME}" \
    "\n\tBASTION_SUBNET=${BASTION_SUBNET}"

# Enable the required APIs
gcloud services enable \
    compute.googleapis.com \
    redis.googleapis.com \
    secretmanager.googleapis.com \
    servicenetworking.googleapis.com \
    vpcaccess.googleapis.com \
    iap.googleapis.com
```

### 2. Create Custom VPC and Dedicated Subnets

```bash
# Create a custom-mode VPC network (no automatic/permissive firewall rules)
gcloud compute networks create ${VPC_NAME} --subnet-mode=custom

# Create subnet for App Engine (for Direct VPC Egress)
gcloud compute networks subnets create ${APPENGINE_SUBNET} \
    --network=${VPC_NAME} \
    --region=${REGION} \
    --range=10.0.1.0/24 \
    --enable-private-ip-google-access

# Create subnet for management / bastion VMs
gcloud compute networks subnets create ${BASTION_SUBNET} \
    --network=${VPC_NAME} \
    --region=${REGION} \
    --range=10.0.2.0/24 \
    --enable-private-ip-google-access

# Allocate an internal IP range for Private Services Access (PSA)
gcloud compute addresses create redis-ip-range \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=24 \
    --network=${VPC_NAME}

# Establish the VPC Peering connection for Google managed services
gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges=redis-ip-range \
    --network=${VPC_NAME}
```

### 3. Configure Firewall Rule for Identity-Aware Proxy (IAP)

Allow SSH access to management VMs **exclusively** from Google's IAP netblock (`35.235.240.0/20`), without exposing port 22 to the public internet:

```bash
gcloud compute firewall-rules create ${VPC_NAME}-allow-iap-ssh \
    --network=${VPC_NAME} \
    --allow=tcp:22 \
    --source-ranges=35.235.240.0/20 \
    --target-tags=bastion \
    --description="Allow SSH ingress exclusively from Google Cloud IAP"
```

### 4. Create Memorystore for Redis Instance

```bash
# Create the Redis instance attached to the custom VPC
gcloud redis instances create ${REDIS_INSTANCE} \
    --size=1 \
    --region=${REGION} \
    --zone=${ZONE} \
    --tier=basic \
    --network=${VPC_NAME} \
    --connect-mode=private-service-access \
    --enable-auth

# Retrieve the Redis private IP Host and Port, and the AUTH (when enabled)
export REDIS_HOST=$(gcloud redis instances describe ${REDIS_INSTANCE} \
    --region=${REGION} --format="value(host)")
export REDIS_PORT=$(gcloud redis instances describe ${REDIS_INSTANCE} \
    --region=${REGION} --format="value(port)")
export REDIS_DB=0
export REDIS_AUTH=$(gcloud redis instances get-auth-string ${REDIS_INSTANCE} \
    --region=${REGION} --format="value(authString)")
echo -e "Redis running at:" \
    "\n\tREDIS_HOST=${REDIS_HOST}\n\tREDIS_PORT=${REDIS_PORT}" \
    "\n\tREDIS_DB=${REDIS_DB}\n\tREDIS_AUTH=${REDIS_AUTH}"

# Create `redis-config` Secret to hold Memorystore for Redis connection details
echo -n "${REDIS_HOST}:${REDIS_PORT}:${REDIS_DB}:${REDIS_AUTH}" | \
    gcloud secrets create redis-config --data-file=-

# Grant IAM Permission to the App Engine Service Account to use the Secret
export APP_SERVICE_ACCOUNT=$(gcloud app describe --format="value(serviceAccount)")
gcloud secrets add-iam-policy-binding redis-config \
    --member="serviceAccount:${APP_SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
```

### 5. App Engine Configuration (`main/app.yaml`)

Update `main/app.yaml` to route private traffic based on the above.

```bash
echo -e "Use the following in your main/app.yaml:" \
    "\nvpc_access:" \
    "\n  network_interface:" \
    "\n    network: projects/${PROJECT_ID}/global/networks/${VPC_NAME}" \
    "\n    subnet: projects/${PROJECT_ID}/regions/${REGION}$/subnetworks/${APPENGINE_SUBNET}" \
    "\n  vpc_egress: private-ranges-only"
```

And copy that output to the `main/app.yaml`:

```yaml
# Direct VPC Egress configuration
vpc_access:
  network_interface:
    network: projects/<YOUR_PROJECT_ID>/global/networks/<YOUR_VPC_NAME>
    subnet: projects/<YOUR_PROJECT_ID>/regions/us-central1/subnetworks/<YOUR_APPENGINE_SUBNET>
  vpc_egress: private-ranges-only
```

## Connecting Shell to Memorystore for Redis

To access Redis using `redis-cli`, create an ephemeral bastion VM inside the private subnet with **no public IP address** and establish an SSH port-forwarding tunnel via Identity-Aware Proxy (IAP). This forwards traffic directly to your local workstation, allowing you to use your local `redis-cli`, Docker, or desktop GUI tool without needing internet access or package managers inside the private VM:

```bash
# Create an ephemeral private VM (no public IP, no IAM service account)
gcloud compute instances create ${BASTION_NAME} \
    --zone=${ZONE} \
    --machine-type=e2-micro \
    --network=${VPC_NAME} \
    --subnet=${BASTION_SUBNET} \
    --tags=bastion \
    --metadata=VmDnsSetting=ZonalOnly \
    --no-address \
    --no-service-account \
    --no-scopes

# Establish a background SSH port-forwarding tunnel via IAP
# NOTE: To address a possible performance warning, add NumPy to gcloud with:
#   $(gcloud info --format="value(basic.python_location)") -m pip install numpy
gcloud compute ssh ${BASTION_NAME} \
    --zone=${ZONE} \
    --tunnel-through-iap \
    -- -N -L 6379:${REDIS_HOST}:6379 &
TUNNEL_PID=$!

# Connect from your local terminal using redis-cli (or via Docker)
redis-cli -h 127.0.0.1 -p 6379
# Alternatively, if redis-cli is not installed locally, use Docker:
docker run -it --rm --network host redis:7.2 redis-cli -h 127.0.0.1 -p 6379 -a ${REDIS_AUTH}

# Check server info and cached keys
INFO
KEYS *gae-init*
exit

# Stop the tunnel and delete the bastion VM
kill $TUNNEL_PID
gcloud compute instances delete ${BASTION_NAME} --zone=${ZONE} --quiet

# Verify it is removed
gcloud compute instances list
```

## Clean up Memorystore and VPC

To avoid charges when finished testing, tear down resources in reverse dependency order.

When tearing down Direct VPC Egress, deleting the App Engine subnet immediately after deleting the App Engine version will fail with an already being used by serverless-ipv4-... error. Google Cloud retains serverless IP reservations for 1–2 hours before releasing them. Run the subnet deletion command after this cooldown window has passed.

```bash
# Delete the Redis instance (~$36/month)
gcloud redis instances delete ${REDIS_INSTANCE} \
    --region=${REGION} --quiet

# Delete the Private Services Access peering connection & allocated IP range
gcloud services vpc-peerings delete \
    --service=servicenetworking.googleapis.com \
    --network=${VPC_NAME} --quiet
gcloud compute addresses delete redis-ip-range \
    --global --quiet

# Verify any outstanding Direct VPC Egress assignments
# may take 1-2 hours to release and could block subnet deletion
gcloud compute addresses list --project=${PROJECT_ID} --filter="purpose=SERVERLESS"
# For more details:
export ADDRESS_NAME=<ADDRESS_NAME-from-the-list>
gcloud compute addresses describe ${ADDRESS_NAME} \
    --region=${REGION} --format="json(name, address, status, creationTimestamp, users)"

# Delete the firewall rule and subnets
gcloud compute firewall-rules delete ${VPC_NAME}-allow-iap-ssh --quiet
gcloud compute networks subnets delete ${APPENGINE_SUBNET} \
    --region=${REGION} --quiet
gcloud compute networks subnets delete ${BASTION_SUBNET} \
    --region=${REGION} --quiet

# Delete the custom VPC network
gcloud compute networks delete ${VPC_NAME} --quiet

# Verify resources are removed
gcloud redis instances list --region=${REGION}
gcloud compute networks subnets list --regions=${REGION}
gcloud compute networks list
gcloud compute instances list

# Not expected, as no longer used, but verify for any dedicated VPC Connectors
gcloud compute networks vpc-access connectors list --region=${REGION}
```

## Tech Stack

- [Google App Engine (GAE) Standard][google app engine], [NDB][]
- [Flask][], [Flask-RESTful][], [Flask-WTF][], [Jinja2][]
- [Bootstrap][], [Day.js][], [Font Awesome][], [Social Buttons][]
- [OpenID][] sign in (Google, Facebook, Twitter and more)
- [Python 3][], [just][], [uv][], [ruff][], [ty][]

[bootstrap]: https://getbootstrap.com/
[day.js]: https://day.js.org/
[documentation]: http://docs.gae-init.appspot.com
[feature list]: http://docs.gae-init.appspot.com/features/
[flask-restful]: https://flask-restful.readthedocs.io
[flask-wtf]: https://flask-wtf.readthedocs.io
[flask]: https://flask.palletsprojects.com/
[font awesome]: https://github.com/fortawesome/font-awesome
[google app engine sdk for python]: https://developers.google.com/appengine/downloads
[google app engine]: https://developers.google.com/appengine/
[how to]: http://docs.gae-init.appspot.com/howto/
[jinja2]: https://jinja.palletsprojects.com/
[just]: https://github.com/casey/just
[linux]: https://ubuntu.com/
[macos]: https://www.apple.com/os/macos/
[ndb]: https://developers.google.com/appengine/docs/python/ndb/
[node.js]: http://nodejs.org/
[openid]: http://en.wikipedia.org/wiki/OpenID
[python 3]: https://docs.cloud.google.com/appengine/docs/standard/python3/runtime
[ruff]: https://github.com/astral-sh/ruff
[rust-just]: https://github.com/casey/just/
[social buttons]: https://lipis.github.io/bootstrap-social/
[tutorial]: https://docs.gae-init.appspot.com/tutorial/
[ty]: https://github.com/astral-sh/ty
[uv]: https://github.com/astral-sh/uv
[windows]: https://windows.microsoft.com/
[yarn]: https://yarnpkg.com/
