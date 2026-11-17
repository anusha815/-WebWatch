# WebWatch – Website Uptime Monitoring System

WebWatch is a Flask mini-project for registering website URLs, manually checking availability, measuring response time, and viewing recent monitoring history.

## Features
- Add and delete website URLs.
- Check one website or all registered websites.
- Show Online/Offline status and HTTP status code.
- Measure response time in milliseconds.
- Store the latest 10 checks in SQLite history.
- Health endpoint: `/health`.
- Automated tests with Pytest.
- GitHub Actions CI workflow.

## Run locally on macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000.

## Run tests
```bash
pytest -q
```

## Push to GitHub
Create an empty repository on GitHub, then:
```bash
git init
git add .
git commit -m "Initial WebWatch project"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```
GitHub Actions automatically runs Pytest on pushes and pull requests to `main` or `master`.

## Deployment
Push the project to GitHub, create a Render Web Service from that repository, and use:
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

The included `render.yaml` contains a deployment blueprint. SQLite files on some free hosting instances may be temporary; persistent storage or a managed database is needed for long-term production use.

## Demo sequence
1. Open the dashboard.
2. Add `https://example.com`.
3. Click Check and show status and response time.
4. Add a deliberately unreachable URL to demonstrate failure handling.
5. Click Check all websites.
6. Show monitoring history.
7. Open `/health`.
8. Push a small change to GitHub and show the Actions test run.

## Scope note
Checks are user-triggered in this student demo; this is not a continuously running background monitoring service. Website availability depends on network connectivity and the target website.
