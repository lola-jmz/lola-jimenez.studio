
```
lola-jimenez-studio
Deployments
Variables
Metrics
Settings
Filter settings
Filter Settings...

/
Source
Connect Source
Connect your service to a GitHub repo or Docker image

Connect Repo

Connect Image
Root Directory
The subdirectory that is deployed when you deploy from the CLI. Docs↗
Root directory
/
Networking
Public Networking
Access your application over HTTP with the following domains
lola-jimenez-studio-production.up.railway.app
Metal Edge




Domain
lola-jimenez-studio-production
.up.railway.app

Edit Port
Update your domain or choose a target port


Cancel

Update
lola-jimenez.studio



Port 8080

 · 
Metal Edge
Setup complete

Domain
lola-jimenez.studio
Enter the port your app is listening on

Target port
8080
Update your target port


Cancel

Update

Custom Domain

TCP Proxy
You have hit the custom domain limit for your plan. Please upgrade to add more.

Private Networking
Communicate with this service from within the Railway network.
lola-jimenez-studio.railway.internal
IPv4 & IPv6


Ready to talk privately ·
You can also simply call me
lola-jimenez-studio
.

DNS
lola-jimenez-studio
.railway.internal

Endpoint name available!


Cancel

Update
Build
Builder
The value is set in
railway.toml

Dockerfile

Dockerfile

Build with a Dockerfile using BuildKit. Docs↗

Metal Build Environment
Metal

Use our new Metal-based build environment. The new Metal build environment is faster and will be the default for all builds in the coming months.


Watch Paths
Gitignore-style rules to trigger a new deployment based on what file paths have changed. Docs↗
Add pattern
Add pattern e.g. /src/**

Deploy
Custom Start Command
Command that will be run to start new deployments. Docs↗
The value is set in
railway.toml
Start command
sh -c 'uvicorn api.run_fastapi:app --host 0.0.0.0 --port ${PORT:-8000}'
Add pre-deploy step (Docs↗)
Regions
Configure how many instances of this service are deployed in each region.
US West (California, USA)

Replicas
1
Instance
Multi-region replicas are only available on the Pro plan.

Learn More↗
Teardown
Configure old deployment termination when a new one is started. Docs↗

Resource Limits
Max amount of vCPU and Memory to allocate to each replica for this service.
CPU: 2 vCPU

Plan limit: 2 vCPU

Memory: 1 GB

Plan limit: 1 GB

Upgrade to toggle resource limits
Cron Schedule
Run the service according to the specified cron schedule.

Add Schedule
Healthcheck Path
Endpoint to be called before a deploy completes to ensure the new deployment is live. Docs↗
The value is set in
railway.toml
Healthcheck Path
/health
Healthcheck Timeout
Number of seconds we will wait for the healthcheck to complete. Docs↗
The value is set in
railway.toml
Healthcheck Timeout
30
Serverless
Containers will scale down to zero and then scale up based on traffic. Requests while the container is sleeping will be queued and served when the container wakes up. Docs↗

Restart Policy
Configure what to do when the process exits. Docs↗
The value is set in
railway.toml
On Failure

Restart the container if it exits with a non-zero exit code.


Your plan only supports up to 10 retries

Upgrade
Number of times to try and restart the service if it stopped due to an error.
The value is set in
railway.toml
Max restart retries
5
Config-as-code
Railway Config File
Manage your build and deployment settings through a config file. Docs↗
Railway config file path
 railway.json
Delete Service
Deleting this service will permanently delete all its deployments and remove it from this environment. This cannot be undone.

Delete service


