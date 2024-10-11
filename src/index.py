import os
from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
import xml.etree.ElementTree as ET
from .cache import cache_get, cache_get_all
from .coverage import cobertura_get_line_rate, create_badge, get_all_runs, get_and_cache_xml, get_run_id, CoverageDataPoint

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/dashboard/{user}/{repo}")
async def dashboard(user: str, repo: str, branch="main", request: Request = None):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "repo": repo, "branch": branch})


@app.get("/data/{user}/{repo}")
async def read_runs(user: str, repo: str, branch="main"):
    headers = {'Authorization': 'token ' + os.environ.get("API_TOKEN")}
    runs = get_all_runs(user, repo, branch, "coverage.yml",
                        headers, 100, "push")
    run_info = [(run["id"], run["head_commit"], run["created_at"])
                for run in runs["workflow_runs"]]

    cache_keys = [f"coverage:{user}:{repo}:{run[0]}" for run in run_info]

    # get all cached data and fill with live
    result = cache_get_all(cache_keys)
    for i, res in enumerate(result):
        if not res:
            result[i] = get_and_cache_xml(user, repo, run_info[i][0],
                                          headers, cache_keys[i])

    data = [CoverageDataPoint.create(run_info[i], xml)
            for i, xml in enumerate(result)]
    return data


@app.get("/coverage/{user}/{repo}")
async def read_coverage(user: str, repo: str, branch="main",):
    headers = {'Authorization': 'token ' + os.environ.get("API_TOKEN")}

    run_id = get_run_id(user, repo, branch, "coverage.yml", headers)

    cache_key = f"coverage:{user}:{repo}:{run_id}"
    cached_xml = cache_get(cache_key)

    if cached_xml:
        tree = ET.ElementTree(ET.fromstring(cached_xml))
    else:
        tree = get_and_cache_xml(user, repo, run_id, headers, cache_key)

    line_rate_float = cobertura_get_line_rate(tree)

    badge = create_badge(line_rate_float)

    response_headers = {
        "Surrogate-Control": "max-age=3600",
        "Cache-Control": "public, max-age=600, s-maxage=600, stale-while-revalidate=30",
    }
    return Response(badge, media_type="image/svg+xml", headers=response_headers)


@app.get("/{full_path:path}")
async def catch_all(request: Request):
    with open("static/index.html") as f:
        return HTMLResponse(f.read(), status_code=200)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)
