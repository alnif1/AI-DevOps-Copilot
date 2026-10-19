# AI DevOps Copilot

Run the frontend, API, and PostgreSQL database together with Docker Compose:

```powershell
docker compose up --build
```

Open <http://localhost:8080>. The API documentation is available at
<http://localhost:8000/docs>.

Compose stores PostgreSQL data in the `postgres_data` named volume, so incident
history remains available after containers are stopped or recreated. Stop the
services with `docker compose down`; this leaves the database volume intact.

The default database credentials are for local development only. Override them
with environment variables or a `.env` file before using a non-local
environment:

```dotenv
POSTGRES_DB=opspilot
POSTGRES_USER=opspilot
POSTGRES_PASSWORD=replace-with-a-local-password
```

The frontend is published on port `8080`, the API on port `8000`, Prometheus
on port `9090`, and Alertmanager on localhost port `9093` by default. Set
`FRONTEND_PORT`, `BACKEND_PORT`, or `PROMETHEUS_PORT` to change the configurable
host ports.

## Monitoring

Prometheus, Blackbox Exporter, and Alertmanager are included in the Compose
stack. Prometheus probes the OpsPilot API health endpoint, the example
external URL, and an isolated Nginx `outage-test` service configured in
`monitoring/prometheus/prometheus.yml`. Replace `https://example.com/` with
one or more HTTP/HTTPS endpoints you own or are authorized to monitor.

Open <http://localhost:9090/targets> to check target status. Query
`probe_success` in the Prometheus expression browser: `1` means reachable and
`0` means the probe failed. The `EndpointUnavailable` alert fires after a
target has failed continuously for 30 seconds. Alertmanager forwards firing and
resolved notifications to `POST /api/v1/alerts`. OpsPilot tracks alert
fingerprints and firing cycles in PostgreSQL, creates only one incident for
duplicate firing notifications, updates incident status on resolution, and
shows the alert state in incident history.

To test alert delivery without stopping OpsPilot, start the isolated test
service and wait for its healthy probe, then stop only that service:

```powershell
docker compose up -d outage-test
docker compose stop outage-test
```

After its `EndpointUnavailable` alert fires, restore it and wait for the alert
to resolve:

```powershell
docker compose start outage-test
```

Keep the backend running during this test so it can receive Alertmanager
webhooks.

Blackbox Exporter's host port `9115` is bound to localhost. Prometheus data is
stored in the `prometheus_data` named volume, and Alertmanager state is stored
in `alertmanager_data`; both remain when running `docker compose down`.
Alertmanager is available at <http://localhost:9093>. These development
webhook endpoints are intended for the local Compose network and should be
protected with authentication before exposing the stack to an untrusted
network.
