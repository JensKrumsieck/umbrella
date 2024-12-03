from dataclasses import dataclass
from io import BytesIO
import zipfile
from fastapi import HTTPException
import xml.etree.ElementTree as ET
from pybadges import badge
import requests
from .cache import cache_set
from .util import evaluate_color


@dataclass
class CoveredFile:
    filename: str
    coverage_value: int


@dataclass
class CoverageDataPoint:
    date: str
    commit_id: str
    commit_message: str
    committer: str
    run_id: int
    coverage_value: int
    files: list[CoveredFile]

    def create(run_info, xml):
        date = run_info[2]
        commit_id = run_info[1]["id"]
        committer = run_info[1]["committer"]["name"]
        commit_message = run_info[1]["message"]
        if isinstance(xml, ET.ElementTree):
            xml_tree = xml
        else:
            xml_tree = ET.ElementTree(ET.fromstring(xml))
        value = cobertura_get_line_rate(xml_tree)
        files = cobertura_get_files_rate(xml_tree)
        return CoverageDataPoint(date, commit_id, commit_message, committer, run_info[0], value, files)


def get_all_runs(user: str, repo: str, branch: str, filename: str, headers: any, limit: int = 100, event: str = "") -> str:
    # get workflow runs
    runs_url = f"https://api.github.com/repos/{user}/{repo}/actions/workflows/{filename}/runs?status=success&branch={branch}&per_page={limit}&event={event}"
    response = requests.get(runs_url, headers=headers)
    if not response.ok:
        raise HTTPException(status_code=response.status_code,
                            detail=f"GitHub API returned error. Request URL: {runs_url}")
    run_json = response.json()
    return run_json


def get_run_id(user: str, repo: str, branch: str, filename: str, headers: any) -> str:
    run_json = get_all_runs(user, repo, branch, filename, headers, 1, "push")
    if len(run_json["workflow_runs"]) == 0:
        raise HTTPException(
            status_code=404, detail=f"Could not find any Workflow runs for {filename}")

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


def cobertura_get_files_rate(tree: ET.ElementTree) -> list[CoveredFile]:
    root = tree.getroot()
    classes = []
    for p in root.iter("package"):
        for c in p.iter("class"):
            classes.append(CoveredFile(c.attrib.get("filename"), float(c.get("line-rate")) * 100))
    return classes


def create_badge(value: float):
    color = evaluate_color(value)

    return badge(left_text="coverage",
                 right_text=f"{round(value, 2)} %", right_color=color)


def get_cobertura_xml(user: str, repo: str, run_id: str, headers: any) -> ET.ElementTree:
    zip_url = get_artifact_url(user, repo, run_id, headers)
    zip_file = download_zip_file(zip_url, headers)
    tree = get_xml_from_zip(zip_file)
    return tree


def get_and_cache_xml(user: str, repo: str, run_id: str, headers, cache_key: str):
    tree = get_cobertura_xml(user, repo, run_id, headers)
    tree_str = ET.tostring(
        tree.getroot(), encoding='utf-8').decode('utf-8')
    cache_set(cache_key, tree_str, 30 * 24 * 60 * 60)
    return tree
