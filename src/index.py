from io import BytesIO
import os
import zipfile
from fastapi import FastAPI, Response
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET
from pybadges import badge

load_dotenv()
app = FastAPI()


@app.get("/coverage/{user}/{repo}/{workflow_yaml}")
def read_coverage(user: str, repo: str, workflow_yaml: str, branch="main"):
    # get workflow runs
    runs_url = f"https://api.github.com/repos/{user}/{repo}/actions/workflows/{workflow_yaml}/runs?status=success&branch={branch}&per_page=1&event=push"
    response = requests.get(runs_url)
    run_json = response.json()
    run_id = run_json["workflow_runs"][0]["id"]

    # list artifacts
    artifacts_url = f"https://api.github.com/repos/{user}/{repo}/actions/runs/{run_id}/artifacts?per_page=100"
    response = requests.get(artifacts_url)
    artifacts_json = response.json()

    # pick first artifact and download
    zip_url = artifacts_json["artifacts"][0]["archive_download_url"]
    headers = {'Authorization': 'token ' + os.environ.get("API_TOKEN")}
    response = requests.get(zip_url, headers=headers, stream=True)

    # Extract ZIP file from the response content
    zip_file = BytesIO(response.content)
    line_rate_float = 0
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        xml_file_name = None
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith('.xml'):
                xml_file_name = file_info.filename
                break

        if xml_file_name:
            with zip_ref.open(xml_file_name) as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                line_rate = root.attrib.get('line-rate')
                line_rate_float = float(line_rate)

    color = 'green'

    if line_rate_float < 75:
        color = 'yellow'

    if line_rate_float < 50:
        color = 'red'

    if line_rate_float < 25:
        color = '#8b0000'

    # create badge
    cov = badge(left_text="coverage",
                right_text=f"{round(line_rate_float, 2)} %", right_color=color)
    return Response(cov, media_type="image/svg+xml")
