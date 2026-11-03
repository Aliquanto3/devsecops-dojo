"""`Settings` : objet unique, lu depuis les variables `DEVSECOPS_DOJO_*`."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from devsecops_dojo.config import Settings, get_settings


def test_valeurs_par_defaut_sans_environnement() -> None:
    assert Settings.from_env({}).data_dir is None


def test_lecture_des_variables_prefixees(tmp_path: Path) -> None:
    settings = Settings.from_env({"DEVSECOPS_DOJO_DATA_DIR": str(tmp_path), "DATA_DIR": "ignoré"})
    assert settings.data_dir == tmp_path


def test_reglages_figes() -> None:
    with pytest.raises(ValidationError):
        Settings.from_env({}).data_dir = Path("x")  # type: ignore[misc]


def test_get_settings_unique() -> None:
    assert get_settings() is get_settings()


# --- compatibilité avec l'ancien nom (variables WDS_*, dossier WaveDevSecOps) ---------------


def test_ancienne_variable_lue_en_repli_avec_avertissement(tmp_path: Path) -> None:
    from devsecops_dojo import config

    config._LEGACY_WARNED.discard("WDS_DATA_DIR")
    with pytest.warns(FutureWarning, match="WDS_DATA_DIR.*DEVSECOPS_DOJO_DATA_DIR"):
        settings = Settings.from_env({"WDS_DATA_DIR": str(tmp_path)})
    assert settings.data_dir == tmp_path


def test_avertissement_de_variable_unique(tmp_path: Path, recwarn: pytest.WarningsRecorder) -> None:
    from devsecops_dojo import config

    config._LEGACY_WARNED.discard("WDS_DATA_DIR")
    Settings.from_env({"WDS_DATA_DIR": str(tmp_path)})
    Settings.from_env({"WDS_DATA_DIR": str(tmp_path)})
    assert len([w for w in recwarn if w.category is FutureWarning]) == 1


def test_nouvelle_variable_prime_sans_avertissement(
    tmp_path: Path, recwarn: pytest.WarningsRecorder
) -> None:
    new, old = tmp_path / "new", tmp_path / "old"
    settings = Settings.from_env({"DEVSECOPS_DOJO_DATA_DIR": str(new), "WDS_DATA_DIR": str(old)})
    assert settings.data_dir == new
    assert not [w for w in recwarn if w.category is FutureWarning]


def test_nouvelle_variable_vide_vaut_absente(tmp_path: Path) -> None:
    """Comme les installeurs (`${VAR:-}`) : vide, la nouvelle variable laisse place à l'ancienne."""
    from devsecops_dojo import config

    config._LEGACY_WARNED.discard("WDS_DATA_DIR")
    with pytest.warns(FutureWarning):
        settings = Settings.from_env({"DEVSECOPS_DOJO_DATA_DIR": "", "WDS_DATA_DIR": str(tmp_path)})
    assert settings.data_dir == tmp_path
    assert Settings.from_env({"DEVSECOPS_DOJO_DATA_DIR": "", "WDS_DATA_DIR": ""}).data_dir is None


def _legacy_tree(root: Path) -> Path:
    legacy = root / "WaveDevSecOps"
    (legacy / "workspaces").mkdir(parents=True)
    (legacy / "progress.json").write_text('{"a": 1}', encoding="utf-8")
    (legacy / "workspaces" / "x.txt").write_text("x", encoding="utf-8")
    (legacy / "app").mkdir()
    (legacy / "app" / "old.txt").write_text("clone", encoding="utf-8")
    (legacy / "app.lock").write_text("http://127.0.0.1:1/", encoding="utf-8")
    return legacy


def test_migration_copie_sans_toucher_l_ancien(tmp_path: Path) -> None:
    from devsecops_dojo.config import migrate_legacy_data_dir

    legacy = _legacy_tree(tmp_path)
    target = tmp_path / "DevSecOpsDojo"
    settings = _with_default_dir(Settings(), target)
    assert migrate_legacy_data_dir(settings, legacy) is True
    assert (target / "progress.json").read_text(encoding="utf-8") == '{"a": 1}'
    assert (target / "workspaces" / "x.txt").read_text(encoding="utf-8") == "x"
    assert not (target / "app").exists()
    assert not (target / "app.lock").exists()  # verrou de l'ancienne instance, pas une donnée
    assert (legacy / "progress.json").exists() and (legacy / "app" / "old.txt").exists()
    assert not list(tmp_path.glob("*.migration-*"))
    # Seconde exécution : le nouveau existe, rien ne se passe.
    (target / "progress.json").write_text("changé", encoding="utf-8")
    assert migrate_legacy_data_dir(settings, legacy) is False
    assert (target / "progress.json").read_text(encoding="utf-8") == "changé"


def _with_default_dir(settings: Settings, target: Path) -> Settings:
    class Fixed(Settings):
        def resolved_data_dir(self) -> Path:
            return target

    return Fixed()


def test_migration_ignoree_si_dossier_choisi(tmp_path: Path) -> None:
    from devsecops_dojo.config import migrate_legacy_data_dir

    legacy = _legacy_tree(tmp_path)
    chosen = tmp_path / "choisi"
    assert migrate_legacy_data_dir(Settings(data_dir=chosen), legacy) is False
    assert not chosen.exists()


def test_migration_sans_ancien_dossier(tmp_path: Path) -> None:
    from devsecops_dojo.config import migrate_legacy_data_dir

    settings = _with_default_dir(Settings(), tmp_path / "DevSecOpsDojo")
    assert migrate_legacy_data_dir(settings, tmp_path / "absent") is False
    assert not (tmp_path / "DevSecOpsDojo").exists()


def test_echec_de_copie_n_empeche_pas_le_demarrage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shutil

    from devsecops_dojo.config import migrate_legacy_data_dir

    legacy = _legacy_tree(tmp_path)
    target = tmp_path / "DevSecOpsDojo"
    settings = _with_default_dir(Settings(), target)

    def boom(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("verrou simulé")

    monkeypatch.setattr(shutil, "copytree", boom)
    with pytest.warns(UserWarning, match="verrou simulé"):
        assert migrate_legacy_data_dir(settings, legacy) is False
    assert not target.exists()
    assert (legacy / "progress.json").exists()
    assert not list(tmp_path.glob("*.migration-*"))
