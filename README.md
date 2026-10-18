# Effective Config API

FastAPI endpoint for the config-precedence assignment.

## Precedence

`defaults -> config.development.yaml -> .env -> OS APP_* environment variables -> query-string set overrides`

Example:
`/effective-config?set=port=9000&set=debug=true`

The `api_key` field is always masked as `****`.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000/effective-config?set=port=9000&set=debug=true`.

For deployment platforms such as Render, use build command `pip install -r requirements.txt`
and start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
