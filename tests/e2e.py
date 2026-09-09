"""Run against the full local Compose stack. Creates and removes its own files."""
from io import BytesIO
import os
import time

import httpx
from PIL import Image

BASE_URL = os.getenv("FILEFLOW_URL", "http://localhost:8000")


def wait_for(check, timeout=90):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(1)
    raise AssertionError("Timed out waiting for processing or analytics")


def main():
    created = []
    with httpx.Client(base_url=BASE_URL, timeout=15) as client:
        def get_json(path):
            response = client.get(path)
            response.raise_for_status()
            return response.json()

        def final_status(file_id, status):
            metadata = get_json(f"/api/v1/files/{file_id}")
            if metadata["status"] in {"READY", "FAILED"}:
                assert metadata["status"] == status, metadata
                return metadata
            return None

        try:
            output = BytesIO()
            Image.new("RGB", (900, 300), "green").save(output, "PNG")
            original = output.getvalue()
            response = client.post("/api/v1/files", files={"file": ("sample.png", original, "image/png")})
            assert response.status_code == 201, response.text
            file_id = response.json()["id"]
            created.append(file_id)
            wait_for(lambda: final_status(file_id, "READY"))
            assert get_json(f"/api/v1/files/{file_id}")["status"] == "READY"
            urls = get_json(f"/api/v1/files/{file_id}/download")
            downloaded = client.get(urls["original_url"])
            downloaded.raise_for_status()
            assert downloaded.content == original
            thumbnail_response = client.get(urls["thumbnail_url"])
            thumbnail_response.raise_for_status()
            with Image.open(BytesIO(thumbnail_response.content)) as thumbnail:
                assert thumbnail.format == "JPEG"
                assert thumbnail.size == (400, 133)

            def processed_event():
                events = get_json("/api/v1/analytics/processing?page_size=100")
                return next((event for event in events if event["payload"]["file_id"] == file_id and event["event_type"] == "file.processed"), None)
            wait_for(processed_event)
            uploads = get_json("/api/v1/analytics/uploads?page_size=100")
            assert any(event["payload"]["file_id"] == file_id for event in uploads)
            overview = get_json("/api/v1/analytics/overview")
            assert overview["files_uploaded"] >= 1 and overview["files_processed"] >= 1

            response = client.post("/api/v1/files", files={"file": ("broken.png", b"broken image", "image/png")})
            assert response.status_code == 201, response.text
            failed_id = response.json()["id"]
            created.append(failed_id)
            wait_for(lambda: final_status(failed_id, "FAILED"))
            wait_for(lambda: any(
                event["payload"]["file_id"] == failed_id and event["event_type"] == "file.processing_failed"
                for event in get_json("/api/v1/analytics/processing?page_size=100")
            ))
            assert client.patch(f"/internal/v1/files/{file_id}/failed").status_code == 404
            for item in created[:]:
                assert client.delete(f"/api/v1/files/{item}").status_code == 204
                assert client.get(f"/api/v1/files/{item}").status_code == 404
                created.remove(item)
            assert client.get(urls["original_url"]).status_code == 404
            assert client.get(urls["thumbnail_url"]).status_code == 404
            print("E2E passed: upload -> RabbitMQ -> thumbnail -> callback -> Kafka -> MongoDB -> delete")
        finally:
            for item in created:
                response = client.delete(f"/api/v1/files/{item}")
                if response.status_code not in {204, 404}:
                    print(f"Cleanup pending for {item}: HTTP {response.status_code}")


if __name__ == "__main__":
    main()
