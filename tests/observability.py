"""Check the local Compose monitoring stack after running e2e.py."""
import httpx


with httpx.Client(trust_env=False, timeout=15) as client:
    response = client.get("http://localhost:8000/health")
    response.raise_for_status()
    print("Gateway:", response.json())

    response = client.get("http://localhost:9090/api/v1/targets")
    response.raise_for_status()
    targets = response.json()["data"]["activeTargets"]
    assert len(targets) == 4 and all(target["health"] == "up" for target in targets)
    print("Prometheus: all four services are up")

    response = client.get(
        "http://localhost:3000/api/dashboards/uid/file-flow", auth=("admin", "admin"),
    )
    response.raise_for_status()
    assert response.json()["dashboard"]["title"] == "FileFlow Overview"
    print("Grafana: FileFlow Overview is available")

    response = client.get(
        "http://localhost:3000/api/datasources/proxy/uid/loki/loki/api/v1/query_range",
        auth=("admin", "admin"),
        params={"query": '{service="processor-service"}', "limit": 5},
    )
    response.raise_for_status()
    assert response.json()["data"]["result"], "Processor logs have not reached Loki"
    print("Loki: processor logs are available")
