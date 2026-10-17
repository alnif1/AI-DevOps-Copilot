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

The frontend is published on port `8080` and the API on port `8000` by default.
Set `FRONTEND_PORT` or `BACKEND_PORT` to change those host ports.
