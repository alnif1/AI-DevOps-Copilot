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

The frontend is published on port `8080`, the API on port `8000`, and Prometheus
on port `9090` by default. Set `FRONTEND_PORT`, `BACKEND_PORT`, or
`PROMETHEUS_PORT` to change those host ports.

## Monitoring

Prometheus and Blackbox Exporter are included in the Compose stack. Prometheus
probes the OpsPilot API health endpoint and the example external URL configured
in `monitoring/prometheus/prometheus.yml`. Replace `https://example.com/` with
one or more HTTP/HTTPS endpoints you own or are authorized to monitor.

Open <http://localhost:9090/targets> to check target status. Query
`probe_success` in the Prometheus expression browser: `1` means reachable and
`0` means the probe failed. The `EndpointUnavailable` alert fires after a
target has failed continuously for 30 seconds. Alertmanager/webhook delivery is
not configured yet.

Blackbox Exporter's host port `9115` is bound to localhost. Prometheus data is
stored in the `prometheus_data` named volume and remains when running
`docker compose down`.
