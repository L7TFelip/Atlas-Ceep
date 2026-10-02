# Repository Guidelines

## Project Structure & Module Organization

The application lives in `Atlas-Ceep/`. `backend/app.py` creates and runs the Flask app; `backend/routes/` contains API blueprints, `backend/database/` manages SQLite setup and data, and `backend/auth_utils.py` holds authentication helpers. Server-rendered pages are in `templates/`; browser code, styles, and images are in `static/js/`, `static/css/`, and `static/assets/`. `backend/testes_api.http` contains sample API requests. There is no dedicated automated test directory in the current repository.

## Build, Test, and Development Commands

Run commands from `Atlas-Ceep/` after installing dependencies:

- `python -m venv .venv && source .venv/bin/activate` creates and activates a local environment.
- `pip install -r requirements.txt` installs the pinned Flask dependencies.
- `python -m backend.app` starts the development server; it initializes the SQLite database at `backend/database/atlas.db`.

Use the requests in `backend/testes_api.http` with an HTTP client to exercise API endpoints. There is no configured build pipeline or automated test runner at present.

## Coding Style & Naming Conventions

Follow the existing Python style: four-space indentation, `snake_case` for functions and variables, and Portuguese names where they match the existing domain and API. Keep route handlers in the relevant blueprint and register new blueprints in `backend/routes/__init__.py`. Use parameterized SQL queries, preserve existing database conventions, and keep frontend assets separated by type under `static/`.

## Testing Guidelines

No formal test framework or coverage target is configured. For API changes, add or update a request in `backend/testes_api.http` and verify the expected response against a local development database. For template or JavaScript changes, run the app and check the affected page and interaction in a browser. Avoid committing local SQLite files; they are ignored by Git.

## Commit & Pull Request Guidelines

The available history uses short, informal Portuguese commit subjects (for example, `reestrutura do projeto`). Keep commit subjects concise and focused on one change. Pull requests should describe the user-visible or API impact, list relevant verification steps, link related issues when applicable, and include screenshots for visual changes.

## Security & Configuration

Set `ATLAS_SECRET_KEY` in the environment outside local development; do not commit secrets or `.env` files. The default development key in `backend/app.py` is not suitable for deployment. Treat the SQLite database as local application data and never include it in commits.
