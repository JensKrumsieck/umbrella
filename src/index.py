import os
from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
import xml.etree.ElementTree as ET
from .cache import cache_service
from .coverage import cobertura_get_line_rate, create_badge, get_cobertura_xml, get_run_id

load_dotenv()
app = FastAPI()


@app.get("/coverage/{user}/{repo}")
async def read_coverage(user: str, repo: str, branch="main",):
    headers = {'Authorization': 'token ' + os.environ.get("API_TOKEN")}

    run_id = get_run_id(user, repo, branch, "coverage.yml", headers)

    cache_key = f"coverage:{user}:{repo}:{run_id}"
    r = cache_service()
    try:
        cached_xml = r.get(cache_key)
    except:
        print("Vercel KV: Limit reached!")
        
    if cached_xml:
        tree = ET.ElementTree(ET.fromstring(cached_xml))
    else:
        tree = get_cobertura_xml(user, repo, run_id, headers)
        tree_str = ET.tostring(tree.getroot(), encoding='utf-8').decode('utf-8')
        r.setex(cache_key, 30 * 24 * 60 * 60, tree_str) # cache 1 month

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
