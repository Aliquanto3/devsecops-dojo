"""DevSecOps Dojo : apprendre git, GitHub, la CI/CD et le DevSecOps, hors ligne."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("devsecops-dojo")
except PackageNotFoundError:  # pragma: no cover - paquet non installé
    __version__ = "0.0.0"
