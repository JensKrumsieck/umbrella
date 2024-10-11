from io import BytesIO
import zipfile
from fastapi import HTTPException
import xml.etree.ElementTree as ET
from pybadges import badge
import requests

from src.util import evaluate_color


def get_run_id(user: str, repo: str, branch: str, filename: str, headers: any) -> str:
    # get workflow runs
    runs_url = f"https://api.github.com/repos/{user}/{repo}/actions/workflows/{filename}/runs?status=success&branch={branch}&per_page=1&event=push"
    response = requests.get(runs_url, headers=headers)
    if not response.ok:
        raise HTTPException(status_code=response.status_code,
                            detail=f"GitHub API returned error. Request URL: {runs_url}")
    run_json = response.json()
    if len(run_json["workflow_runs"]) == 0:
        raise HTTPException(
            status_code=404, detail=f"Could not find any Workflow runs for {runs_url}")

    return run_json["workflow_runs"][0]["id"]


def get_artifact_url(user: str, repo: str, run_id: str, headers: any) -> str:
    # list artifacts
    artifacts_url = f"https://api.github.com/repos/{user}/{repo}/actions/runs/{run_id}/artifacts?per_page=100"
    response = requests.get(artifacts_url, headers=headers)
    if not response.ok:
        raise HTTPException(status_code=response.status_code,
                            detail=f"GitHub API returned error. Request URL: {artifacts_url}")
    artifacts_json = response.json()

    # pick first artifact and download
    if len(artifacts_json["artifacts"][0]) == 0:
        raise HTTPException(
            status_code=404, detail=f"Could not find any artifacts")

    return artifacts_json["artifacts"][0]["archive_download_url"]


def download_zip_file(zip_url: str, headers: any) -> BytesIO:
    response = requests.get(zip_url, headers=headers, stream=True)
    if not response.ok:
        raise HTTPException(status_code=response.status_code,
                            detail=f"GitHub API returned error. Request URL: {zip_url}")

    # Extract ZIP file from the response content
    return BytesIO(response.content)


def get_xml_from_zip(zip_file: BytesIO) -> ET.ElementTree:
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        xml_file_name = None
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith('.xml'):
                xml_file_name = file_info.filename
                break
        if xml_file_name:
            with zip_ref.open(xml_file_name) as xml_file:
                tree = ET.parse(xml_file)
        else:
            raise HTTPException(
                status_code=500, detail="Required XML coverage report not found in the artifact ZIP.")
    return tree


def cobertura_get_line_rate(tree: ET.ElementTree) -> float:
    line_rate_float = 0
    root = tree.getroot()
    line_rate = root.attrib.get('line-rate')
    line_rate_float = float(line_rate) * 100

    return line_rate_float


def create_badge(value: float):
    color = evaluate_color(value)

    return badge(left_text="coverage",
                 right_text=f"{round(value, 2)} %", right_color=color)


def get_cobertura_xml(user: str, repo: str, run_id: str, headers: any) -> ET.ElementTree:
    zip_url = get_artifact_url(user, repo, run_id, headers)
    zip_file = download_zip_file(zip_url, headers)
    tree = get_xml_from_zip(zip_file)
    return tree