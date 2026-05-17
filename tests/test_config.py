from src.config import settings, ROOT_DIR


def test_settings_loaded():
    assert settings.infodengue_base_url.startswith("https://")
    assert settings.openmeteo_base_url.startswith("https://")
    assert settings.minio_bucket == "arboviroses"
    assert settings.ollama_model == "llama3"


def test_root_dir_exists():
    assert ROOT_DIR.exists()


def test_duckdb_path_is_absolute():
    assert settings.duckdb_path.is_absolute()