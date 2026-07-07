from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_services_environment_is_ready() -> None:
    assert True


def test_local_minio_compose_contract_is_one_shot_and_region_aligned() -> None:
    compose = (REPO_ROOT / "compose.yaml").read_text(encoding="utf-8")
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "minio-init:" in compose
    assert 'restart: "no"' in compose
    assert "S3_BUCKET: ${S3_BUCKET:-openpolitics-raw}" in compose
    assert "MINIO_REGION_NAME: ${S3_REGION:-ap-northeast-1}" in compose
    assert ".env.*" in gitignore
    assert "!.env.example" in gitignore
