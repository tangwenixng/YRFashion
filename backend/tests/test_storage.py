from backend.core.config import settings
from backend.services.storage import _build_cloud_public_url, resolve_public_file_url


def test_build_cloud_public_url_prefers_explicit_public_base(monkeypatch) -> None:
    monkeypatch.setattr(
        settings,
        "storage_public_base_url",
        "https://img.example.com/",
        raising=False,
    )
    monkeypatch.setattr(settings, "storage_bucket", "demo-bucket", raising=False)
    monkeypatch.setattr(settings, "storage_region", "ap-shanghai", raising=False)

    public_url = _build_cloud_public_url("products/1/cover.png")

    assert public_url == "https://img.example.com/products/1/cover.png"


def test_build_cloud_public_url_defaults_to_cloudbase_domain(monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_public_base_url", None, raising=False)
    monkeypatch.setattr(settings, "storage_bucket", "demo-bucket", raising=False)
    monkeypatch.setattr(settings, "storage_region", "ap-shanghai", raising=False)

    public_url = _build_cloud_public_url("products/1/cover.png")

    assert public_url == "https://demo-bucket.tcb.qcloud.la/products/1/cover.png"


def test_resolve_public_file_url_prefers_storage_path_for_cloudbase(monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_public_base_url", None, raising=False)
    monkeypatch.setattr(settings, "storage_bucket", "demo-bucket", raising=False)
    monkeypatch.setattr(settings, "storage_region", "ap-shanghai", raising=False)

    public_url = resolve_public_file_url(
        "cloudbase",
        "products/1/cover.png",
        "https://legacy-bucket.cos.ap-shanghai.myqcloud.com/products/1/cover.png",
    )

    assert public_url == "https://demo-bucket.tcb.qcloud.la/products/1/cover.png"


def test_resolve_public_file_url_rebuilds_local_upload_url() -> None:
    public_url = resolve_public_file_url(
        "local",
        "products/1/cover.png",
        "https://legacy.example.com/products/1/cover.png",
    )

    assert public_url == "/uploads/products/1/cover.png"
