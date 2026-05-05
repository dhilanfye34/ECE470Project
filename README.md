# ECE 470 Restaurant gRPC Ordering System

This project is a restaurant ordering system built with Python and gRPC. It includes a containerized backend service, generated gRPC protocol files, a local command-line client, and a local Tkinter GUI client.

The backend can run locally, in Docker, or on Google Cloud Run. The GUI and CLI clients run locally and connect either to `localhost:50000` or to the hosted Cloud Run backend.

No API keys, service account keys, or private credentials should be committed to this repository.

## Project Structure

```text
client/      Command-line gRPC client
frontend/    Tkinter GUI client
gRPC/        Generated protobuf and gRPC Python files
server/      Restaurant gRPC backend and JSON seed data
```

The backend stores menu and order data in JSON. Locally, it reads and writes `server/menu.json` and `server/orders.json`. In Google Cloud, it uses Cloud Storage when `GCS_BUCKET_NAME` is set.

## Local Python Setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run a syntax check:

```powershell
python -m py_compile server\server.py client\client.py frontend\client_gui.py
```

Start the backend locally:

```powershell
python server\server.py
```

In a second terminal, start the GUI client:

```powershell
python frontend\client_gui.py
```

By default, clients connect to:

```text
localhost:50000
```

Useful demo logins:

```text
m1 / manager
s1 / server
c1 / chef
```

## Local Docker Backend

Build and run the backend container:

```powershell
docker compose up --build
```

The Docker Compose service maps the backend to:

```text
localhost:50000
```

Then run the GUI client locally:

```powershell
python frontend\client_gui.py
```

Stop the container:

```powershell
docker compose down
```

## Connect The GUI To The Hosted Backend

The GUI reads the backend address from `RESTAURANT_SERVER_ADDR`.

For a Cloud Run backend, use the Cloud Run hostname with port `443`. Do not include `https://`.

```powershell
$env:RESTAURANT_SERVER_ADDR="<cloud-run-service-host>.a.run.app:443"
python frontend\client_gui.py
```

Example format:

```text
restaurant-server-example-uc.a.run.app:443
```

The client automatically uses TLS for `.run.app` and `:443` addresses. For local testing, leave `RESTAURANT_SERVER_ADDR` unset or set it to `localhost:50000`.

To switch back to local Docker in the same terminal:

```powershell
Remove-Item Env:\RESTAURANT_SERVER_ADDR
python frontend\client_gui.py
```

## Hosted Backend Deployment Notes

The backend is designed to deploy to Google Cloud Run as a gRPC service.

Required Google Cloud resources:

```text
Cloud Run service
Artifact Registry Docker repository
Cloud Storage bucket for menu.json and orders.json
Cloud Build access for image builds
```

## Troubleshooting

- If the GUI cannot connect locally, make sure the backend is running on `localhost:50000`.
- If connecting to Cloud Run, `RESTAURANT_SERVER_ADDR` must not include `https://`.
- If Cloud Run returns connection errors, confirm the service was deployed with `--use-http2`.
- If Cloud Storage reads or writes fail, check the Cloud Run service account permissions for the bucket.
- If Docker is not found in VS Code, restart VS Code after installing Docker Desktop.

## Security Notes

- Do not commit service account JSON files.
- Do not commit API keys, access tokens, or private credentials.
- Keep Google Cloud project IDs, bucket names, and service URLs as local environment variables or placeholders in shared documentation.
- Cloud Run is deployed with `--allow-unauthenticated` for demo access; the app still uses role-based login IDs internally.
