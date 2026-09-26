"""Deploy the CI-built image via Render REST API, without CLI or deploy hooks."""

import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Configure {name} in GitHub Actions before deploying")
    return value


def api(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    request = Request(
        f"https://api.render.com/v1/{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        data=json.dumps(payload).encode() if payload is not None else None,
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        # Do not log response bodies, which can contain service configuration.
        raise RuntimeError(f"Render API {method} {path}: HTTP {exc.code}") from None


def wait_for_deploy(service_id: str, deploy_id: str, token: str) -> None:
    deadline = time.monotonic() + 20 * 60
    pending = {
        "created", "queued", "build_in_progress", "build_succeeded",
        "pre_deploy_in_progress", "pre_deploy_succeeded", "update_in_progress",
    }
    while time.monotonic() < deadline:
        result = api("GET", f"services/{service_id}/deploys/{deploy_id}", token)
        status = result["status"]
        print(f"Render deploy {deploy_id}: {status}", flush=True)
        if status == "live":
            return
        if status not in pending:
            raise RuntimeError(f"Deploy did not succeed: {status}")
        time.sleep(10)
    raise RuntimeError("Timed out waiting for Render deployment")


def wait_for_api(base_url: str) -> None:
    deadline = time.monotonic() + 5 * 60
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{base_url}/api/v1/persons", timeout=30) as response:
                if response.status == 200 and isinstance(json.load(response), list):
                    print("Deployed API and database are ready", flush=True)
                    return
        except (URLError, TimeoutError, ValueError):
            pass
        time.sleep(10)
    raise RuntimeError("Deployed API did not become ready")


def main() -> None:
    token = required("RENDER_API_KEY")
    service_id = required("RENDER_SERVICE_ID")
    base_url = required("RENDER_SERVICE_URL").rstrip("/")
    image_url = required("IMAGE_URL")
    if not re.fullmatch(r"srv-[a-z0-9]+", service_id):
        raise RuntimeError("Invalid Render service ID")
    if not re.fullmatch(r"https://[a-z0-9-]+\.onrender\.com", base_url):
        raise RuntimeError("RENDER_SERVICE_URL must be the service's onrender.com URL")
    if not re.fullmatch(r"ghcr\.io/[a-z0-9._/-]+@sha256:[a-f0-9]{64}", image_url):
        raise RuntimeError("IMAGE_URL must identify the CI-built GHCR image by digest")

    service = api("GET", f"services/{service_id}", token)
    if service.get("repo"):
        raise RuntimeError(
            "This service builds from Git. Configure an Existing Image service "
            "so that the image is built only in GitHub Actions."
        )
    details = service.get("serviceDetails", {})
    if details.get("url", "").rstrip("/") != base_url:
        raise RuntimeError("RENDER_SERVICE_URL does not match RENDER_SERVICE_ID")
    if details.get("envSpecificDetails", {}).get("dockerCommand"):
        raise RuntimeError("Clear Render Docker Command to use the image's migration/start command")

    deploy = api("POST", f"services/{service_id}/deploys", token, {"imageUrl": image_url})
    wait_for_deploy(service_id, deploy["id"], token)
    wait_for_api(base_url)


if __name__ == "__main__":
    main()
