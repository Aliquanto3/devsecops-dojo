"""Scénarios déclaratifs (AD-7) : modèle YAML, registre d'ops de setup, alias.

`scenarios` dépend de `gitio` (git en contexte interne) et de `wsfs` (fichiers en LF) ;
il ne lance aucun processus et n'écrit aucun fichier lui-même.
"""

from devsecops_dojo.scenarios.context import PERSONAS, SETUP_EPOCH, SetupContext, SetupError
from devsecops_dojo.scenarios.loader import (
    FieldError,
    LoadedScenario,
    ScenarioError,
    load_scenario,
    parse_scenario,
    scenario_files,
)
from devsecops_dojo.scenarios.model import SCHEMA_VERSION, Scenario, StepSpec
from devsecops_dojo.scenarios.ops import REGISTRY
from devsecops_dojo.scenarios.setup import run_setup
from devsecops_dojo.scenarios.steps import STEP_TYPES

__all__ = [
    "PERSONAS",
    "REGISTRY",
    "SCHEMA_VERSION",
    "SETUP_EPOCH",
    "STEP_TYPES",
    "FieldError",
    "LoadedScenario",
    "Scenario",
    "ScenarioError",
    "SetupContext",
    "SetupError",
    "StepSpec",
    "load_scenario",
    "parse_scenario",
    "run_setup",
    "scenario_files",
]
