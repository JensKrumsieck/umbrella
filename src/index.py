import os
from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse

from .coverage import cobertura_get_line_rate, create_badge, get_artifact_url, download_zip_file, get_run_id

load_dotenv()
app = FastAPI()


@app.get("/coverage/{user}/{repo}")
def read_coverage(user: str, repo: str, branch="main"):
    headers = {'Authorization': 'token ' + os.environ.get("API_TOKEN")}

    run_id = get_run_id(user, repo, branch, "coverage.yml", headers)

    zip_url = get_artifact_url(user, repo, run_id, headers)

    zip_file = download_zip_file(zip_url, headers)

    line_rate_float = cobertura_get_line_rate(zip_file)

    badge = create_badge(line_rate_float)

    return Response(badge, media_type="image/svg+xml")


@app.get("/{full_path:path}")
async def catch_all(request: Request):
    with open("static/index.html") as f:
        return HTMLResponse(f.read(), status_code=200)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)
