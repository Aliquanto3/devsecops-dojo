"""Réglages de l'application : un seul objet `Settings`, seul lecteur de l'environnement.

Module feuille (AD-1) : il n'importe rien du projet. Aucun autre module ne lit
`os.environ` ni `os.getenv` (convention « Réglages » du spine) ; ils reçoivent un
`Settings`, ou appellent `get_settings()`.

Chaque champ peut être fixé par une variable d'environnement `DEVSECOPS_DOJO_<NOM_DU_CHAMP>`
(par exemple `DEVSECOPS_DOJO_DATA_DIR`).

Compatibilité (ancien nom du projet) : les variables `WDS_<NOM_DU_CHAMP>` restent lues quand la
variable `DEVSECOPS_DOJO_*` correspondante est absente (avertissement unique), et l'ancien
dossier de données est copié vers le nouveau au premier lancement
(`migrate_legacy_data_dir`). Tout le code
de compatibilité est dans ce module ; il disparaîtra avec l'ancien nom.
"""

from __future__ import annotations

import os
import shutil
import warnings
from collections.abc import Mapping
from functools import cache
from pathlib import Path

from platformdirs import user_data_dir
from pydantic import BaseModel, ConfigDict, Field, field_validator

ENV_PREFIX = "DEVSECOPS_DOJO_"
APP_NAME = "DevSecOpsDojo"
LEGACY_ENV_PREFIX = "WDS_"
LEGACY_APP_NAME = "WaveDevSecOps"
LEGACY_SKIPPED = ("app", "app.lock")
"""Entrées de l'ancien dossier non copiées : `app/` (réinstallé) et `app.lock` (verrou de
l'instance en cours, propre à l'ancien dossier)."""
LEGACY_NETGUARD_VARIABLE = "WDS_NETGUARD"
"""Variable lue par la garde réseau des environnements d'exercice créés avant le renommage
(`_wds_netguard`, copiés par la migration) : posée avec la nouvelle pour qu'ils restent gardés."""
_LEGACY_WARNED: set[str] = set()
PROXY_VARIABLES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "UV_SYSTEM_CERTS")


def project_root() -> Path:
    """Racine du dépôt (clone ou zip) : là où vivent `tools.toml` et `content/`."""
    return Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    """Réglages de DevSecOps Dojo. Les stories suivantes y ajoutent leurs champs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    data_dir: Path | None = None
    """Dossier des données utilisateur ; `None` : dossier par défaut de platformdirs."""

    @field_validator("data_dir", mode="before")
    @classmethod
    def _empty_data_dir(cls, value: object) -> object:
        """`DEVSECOPS_DOJO_DATA_DIR=""` vaut « non fixé », pas le répertoire courant."""
        return None if isinstance(value, str) and not value.strip() else value

    log_max_bytes: int = 1_000_000
    """Taille d'un fichier de `<data>/logs/app.log` avant rotation."""

    log_backup_count: int = 3
    """Nombre de fichiers de journal conservés après rotation."""

    def resolved_data_dir(self) -> Path:
        """Dossier des données : `data_dir`, sinon celui de platformdirs (AD-5)."""
        if self.data_dir is not None:
            return self.data_dir
        return Path(user_data_dir(APP_NAME, appauthor=False, roaming=False))

    tools_file: Path | None = None
    """Registre d'outils (AD-16) ; `None` : `tools.toml` à la racine du dépôt."""

    content_dir: Path | None = None
    """Dossier `content/` ; `None` : `content/` à la racine du dépôt."""

    probe_timeout_s: float = 10.0
    """Délai maximal d'une sonde d'outil (version, locale, `xcode-select`), en secondes."""

    git_timeout_s: float = 30.0
    """Délai maximal d'une commande git interne (setup, lectures de l'empreinte), en secondes."""

    event_buffer: int = Field(default=1000, ge=1)
    """Événements gardés par espace pour la reprise du flux SSE (`Last-Event-ID`, AD-17)."""

    max_active_workspaces: int = Field(default=3, ge=1)
    """Espaces actifs (file, surveillant, runs) au plus ; les autres dorment (AD-1)."""

    max_pending_ops: int = Field(default=32, ge=1)
    """Opérations en attente dans la file d'un espace avant de refuser une intention (409)."""

    watch_quiet_ms: int = Field(default=300, ge=0)
    """Silence après une commande avant que le surveillant de l'arbre reprenne (AD-1)."""

    sse_heartbeat_s: float = Field(default=15.0, gt=0)
    """Intervalle des lignes de maintien du flux SSE, en secondes."""

    engine_stop_timeout_s: float = Field(default=30.0, gt=0)
    """Attente maximale de la fin de l'opération en cours quand un espace s'endort."""

    terminal_timeout_s: float = Field(default=30.0, gt=0)
    """Délai d'une commande tapée dans le terminal ; au-delà, l'arbre est arrêté (AD-4, AD-12)."""

    tool_timeout_s: float = Field(default=120.0, gt=0)
    """Délai d'un outil de la chaîne (ruff, pytest) lancé depuis le terminal (AD-4, AD-12)."""

    pipeline_job_timeout_s: float = Field(default=120.0, gt=0)
    """Délai d'un job du pipeline simulé ; au-delà, l'arbre est arrêté et le check est en
    erreur de l'outil (AD-10, AD-12)."""

    max_snapshots: int = Field(default=20, ge=2)
    """Instantanés gardés par espace ; le 0 et le dernier le sont toujours (AD-6)."""

    restore_retry_ms: int = Field(default=250, ge=0)
    """Pause avant le 2e essai d'un renommage de restauration (doublée avant le 3e, AD-6)."""

    llm_run_timeout_s: float = Field(default=180.0, gt=0)
    """Délai maximal du code d'exercice du parcours LLM lancé par l'apprenant (AD-13)."""

    def gitconfig_path(self) -> Path:
        """`<data>/gitconfig`, désigné par `GIT_CONFIG_GLOBAL` (AD-3, AD-5)."""
        return self.resolved_data_dir() / "gitconfig"

    def workspaces_path(self) -> Path:
        """`<data>/workspaces/` : un espace par parcours, scénario et mode (AD-5)."""
        return self.resolved_data_dir() / "workspaces"

    def scenarios_path(self) -> Path:
        """`content/scenarios/` : un YAML par scénario et par mode (AD-7)."""
        return self.content_path() / "scenarios"

    def pipeline_path(self) -> Path:
        """`content/pipeline.yaml` : le pipeline simulé, décrit une seule fois (AD-10)."""
        return self.content_path() / "pipeline.yaml"

    def ci_config_path(self) -> Path:
        """`content/ci/` : réglages des outils du pipeline (bandit, coverage), hors de l'arbre de
        l'apprenant, jeton `{config}` (story 8.4) : il ne peut pas les remplacer."""
        return self.content_path() / "ci"

    def osv_path(self) -> Path:
        """`content/osv/` : l'extrait figé de la base de vulnérabilités (AD-11)."""
        return self.content_path() / "osv"

    def osv_url(self, port: int) -> str:
        """URL du point OSV local pour le serveur sur `port` : la seule source (AD-11)."""
        return f"http://127.0.0.1:{port}/osv/v1/query"

    def tools_path(self) -> Path:
        return self.tools_file if self.tools_file is not None else project_root() / "tools.toml"

    def content_path(self) -> Path:
        return self.content_dir if self.content_dir is not None else project_root() / "content"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Réglages depuis les variables `DEVSECOPS_DOJO_*` (par défaut `os.environ`)."""
        source = os.environ if environ is None else environ
        values: dict[str, str] = {}
        for name in cls.model_fields:
            key = ENV_PREFIX + name.upper()
            legacy_key = LEGACY_ENV_PREFIX + name.upper()
            # Vide vaut absente, comme dans les installeurs (`${VAR:-}`) : l'ancienne variable
            # sert alors de repli, puis le défaut.
            if source.get(key):
                values[name] = source[key]
            elif source.get(legacy_key):
                _warn_legacy_variable(legacy_key, key)
                values[name] = source[legacy_key]
            elif key in source:
                values[name] = source[key]
        return cls.model_validate(values)


def _warn_legacy_variable(legacy_key: str, key: str) -> None:
    """Avertit une fois par variable : `FutureWarning`, visible sans filtre particulier."""
    if legacy_key in _LEGACY_WARNED:
        return
    _LEGACY_WARNED.add(legacy_key)
    warnings.warn(
        f"La variable d'environnement {legacy_key} est dépréciée : utilisez {key}.",
        FutureWarning,
        stacklevel=3,
    )


def legacy_data_dir() -> Path:
    """Ancien dossier de données par défaut (nom `WaveDevSecOps`), jamais modifié."""
    return Path(user_data_dir(LEGACY_APP_NAME, appauthor=False, roaming=False))


def migrate_legacy_data_dir(settings: Settings, legacy: Path | None = None) -> bool:
    """Copie l'ancien dossier de données vers le nouveau, une seule fois.

    Rien si l'utilisateur a choisi son dossier (`data_dir`), si le nouveau existe déjà ou si
    l'ancien est absent. Ne sont pas copiés : le sous-dossier `app/` (clone et environnement de
    l'ancien installeur), le verrou `app.lock` et les environnements Python (dossiers à
    `pyvenv.cfg` : chemins absolus, recréés hors ligne au premier usage). La copie passe par un
    dossier de travail propre au processus puis un renommage : un échec (`OSError` : verrou
    Windows, disque plein, lancement concurrent) ne bloque jamais le démarrage, laisse l'ancien
    dossier intact et émet un avertissement.
    Renvoie vrai si la copie a eu lieu.
    """
    if settings.data_dir is not None:
        return False
    target = settings.resolved_data_dir()
    source = legacy if legacy is not None else legacy_data_dir()
    if target.exists() or not source.is_dir():
        return False
    staging = target.with_name(f"{target.name}.migration-{os.getpid()}")

    def ignore(directory: str, names: list[str]) -> set[str]:
        here = Path(directory)
        skipped = set(LEGACY_SKIPPED) & set(names) if here == source else set()
        # Environnements Python (`cache/venv`, `ci/venv-*`…) : chemins absolus vers l'ancien
        # dossier, non déplaçables ; recréés hors ligne au premier usage.
        return skipped | {name for name in names if (here / name / "pyvenv.cfg").is_file()}

    try:
        shutil.rmtree(staging, ignore_errors=True)
        shutil.copytree(source, staging, ignore=ignore)
        staging.rename(target)
    except OSError as exc:
        shutil.rmtree(staging, ignore_errors=True)
        warnings.warn(
            f"Les données de l'ancienne version ({source}) n'ont pas pu être copiées vers "
            f"{target} ({exc}). L'application démarre avec un dossier de données neuf ; "
            "l'ancien dossier n'est pas modifié.",
            UserWarning,
            stacklevel=2,
        )
        return False
    return True


@cache
def get_settings() -> Settings:
    """Réglages du processus courant, lus une fois."""
    return Settings.from_env()


def read_proxy_environment(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Variables de proxy posées (casse ignorée), sous leur nom en majuscules."""
    source = os.environ if environ is None else environ
    found: dict[str, str] = {}
    for name, value in source.items():
        upper = name.upper()
        if upper not in PROXY_VARIABLES or not value.strip():
            continue
        if upper == "NO_PROXY" and upper in found:
            # `NO_PROXY` et `no_proxy` peuvent différer : les outils lisent l'une ou l'autre,
            # on garde donc l'union de leurs entrées plutôt que la première rencontrée.
            known = [e.strip() for e in found[upper].split(",")]
            extra = [e.strip() for e in value.split(",") if e.strip() not in known]
            found[upper] = ",".join(known + extra)
        else:
            found.setdefault(upper, value.strip())
    return found


def inherited_environment(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Copie de l'environnement du processus, point de départ de celui d'un outil."""
    return dict(os.environ if environ is None else environ)
