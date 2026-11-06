"""Garde-fous de la charte générique v2.1 sur l'interface web.

Jetons, contrastes, boutons, polices. Le calcul des contrastes suit la formule WCAG 2.1, en
bibliothèque standard. Les couples sont une liste explicite, tirée des feuilles de style,
vérifiée dans le thème sombre et dans le thème clair.
"""

from __future__ import annotations

import re

import pytest
from static_rules import STATIC
from test_shell_ui import _palettes, _ratio

CSS = STATIC / "css"
TOKENS = CSS / "tokens.css"

# (texte, fond) : seuil 4,5:1.
TEXT_PAIRS = (
    ("ink", "surface"),
    ("ink", "surface-raised"),
    ("ink-soft", "surface"),
    ("ink-soft", "surface-raised"),
    ("muted", "surface-raised"),
    ("primary", "surface-raised"),  # lien
    ("primary-deep", "primary-soft"),
    ("on-button", "button"),  # bouton principal et bouton à bascule actif
    ("on-button", "button-hover"),
    ("on-ink", "ink-fill"),
    ("on-primary", "primary"),
    ("on-status", "danger"),  # pastille du diagnostic
    ("danger", "danger-soft"),
    ("success", "success-soft"),
    ("ink", "discipline-harness-soft"),
    ("terminal-fg", "terminal-bg"),
    ("terminal-fg-soft", "terminal-bg"),
    ("terminal-accent", "terminal-bg"),
    ("terminal-danger", "terminal-bg"),
)

# (marque, fond) : seuil 3:1 (traits de champ, focus, filet, points, pastilles, icônes).
NON_TEXT_PAIRS = (
    ("line-strong", "surface-raised"),  # contour du bouton secondaire et des champs
    ("line-strong", "surface"),
    ("focus", "surface"),
    ("focus", "surface-raised"),
    ("focus", "primary-soft"),
    ("focus-on-ink", "ink-fill"),
    ("focus-on-ink", "terminal-bg"),
    ("rule", "surface"),  # filet or sous le titre
    ("picto-dot", "picto-tile"),  # point du pictogramme
    ("picto-bars", "picto-tile"),
    ("success", "surface-raised"),  # pastilles d'état
    ("danger", "surface-raised"),
    ("discipline-prompt", "surface-raised"),
    ("discipline-context", "surface-raised"),
    ("discipline-harness", "surface-raised"),
    ("terminal-rule", "terminal-bg"),
    ("terminal-lit-ring", "terminal-bg"),
)


@pytest.fixture(scope="module")
def palettes() -> dict[str, dict[str, str]]:
    return _palettes(TOKENS.read_text(encoding="utf-8"))


@pytest.mark.parametrize("theme", ["clair", "sombre"])
def test_texte_a_4_5_pour_1(palettes: dict[str, dict[str, str]], theme: str) -> None:
    palette = palettes[theme]
    low = [
        f"{fg}/{bg} {_ratio(palette[fg], palette[bg]):.2f}"
        for fg, bg in TEXT_PAIRS
        if _ratio(palette[fg], palette[bg]) < 4.5
    ]
    assert low == []


@pytest.mark.parametrize("theme", ["clair", "sombre"])
def test_marques_non_textuelles_a_3_pour_1(palettes: dict[str, dict[str, str]], theme: str) -> None:
    palette = palettes[theme]
    low = [
        f"{fg}/{bg} {_ratio(palette[fg], palette[bg]):.2f}"
        for fg, bg in NON_TEXT_PAIRS
        if _ratio(palette[fg], palette[bg]) < 3
    ]
    assert low == []


def test_les_deux_themes_different(palettes: dict[str, dict[str, str]]) -> None:
    assert palettes["sombre"]["surface"] == "#0F1318"
    assert palettes["clair"]["surface"] == "#F6F8FB"
    assert palettes["sombre"]["button"] == "#E8ECF2"  # bouton principal neutre
    assert palettes["clair"]["button"] == "#121821"
    assert palettes["sombre"]["focus"] != palettes["clair"]["focus"]


def test_le_terminal_reste_sombre_dans_les_deux_themes(
    palettes: dict[str, dict[str, str]],
) -> None:
    for name in ("terminal-bg", "terminal-fg", "terminal-accent", "terminal-lit-ring"):
        assert palettes["clair"][name] == palettes["sombre"][name], name


def test_aucun_hex_litteral_hors_des_jetons() -> None:
    offenders = [
        f"{path.name}: {hexa}"
        for path in sorted(CSS.glob("*.css"))
        if path.name != "tokens.css"
        for hexa in re.findall(r"#[0-9a-fA-F]{3,8}\b", path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
    assert not re.search(
        r"rgba?\(",
        "".join(p.read_text(encoding="utf-8") for p in CSS.glob("*.css") if p.name != "tokens.css"),
    )


def test_le_bleu_n_est_jamais_un_aplat_de_bouton() -> None:
    """Aucune règle de bouton, de pastille à bascule ou de déclencheur n'a d'aplat `primary`."""
    button_like = re.compile(r"btn|button|pill|trigger|toggle|armed|menu")
    offenders = []
    for path in sorted(CSS.glob("*.css")):
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", path.read_text(encoding="utf-8")):
            if button_like.search(selector) and re.search(
                r"background(?:-color)?:\s*var\(--color-primary\)", body
            ):
                offenders.append(f"{path.name}: {selector.strip()}")
    assert offenders == []


def test_bouton_principal_neutre() -> None:
    shell = (CSS / "shell.css").read_text(encoding="utf-8")
    rule = shell[shell.index(".btn-primary {") :].split("}")[0]
    assert "background: var(--color-button);" in rule
    assert "color: var(--color-on-button);" in rule
    secondary = shell[shell.index(".btn-secondary {") :].split("}")[0]
    assert "border-color: var(--color-line-strong);" in secondary


def test_focus_et_filet_or() -> None:
    shell = (CSS / "shell.css").read_text(encoding="utf-8")
    focus = shell[shell.index(":focus-visible {") :].split("}")[0]
    assert "var(--color-focus)" in focus
    filet = shell[shell.index("main h1::after") :].split("}")[0]
    assert "width: 96px" in filet and "height: 4px" in filet and "var(--color-rule)" in filet


def test_polices_de_la_charte_et_fredoka_retiree() -> None:
    fonts = STATIC / "fonts"
    assert (fonts / "sora-600.woff2").is_file() and (fonts / "OFL-sora.txt").is_file()
    assert not list(fonts.glob("*redoka*"))
    css = (CSS / "fonts.css").read_text(encoding="utf-8")
    assert 'font-family: "Sora";' in css and "font-weight: 600;" in css
    assert "Fredoka" not in css and "Fredoka" not in TOKENS.read_text(encoding="utf-8")


def test_favicon_et_pictogramme_de_la_charte() -> None:
    favicon = (STATIC / "favicon.svg").read_text(encoding="utf-8")
    assert "#3B6FD0" in favicon and "#1D5BC2" in favicon  # tuile sombre, tuile claire
    assert "prefers-color-scheme: light" in favicon
    index = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "var(--color-picto-tile)" in index and "var(--color-picto-dot)" in index
    assert 'fill="var(--color-picto-tile)"' in index  # attribut : un `style` en ligne est refusé
    assert not re.search(r'(?:fill|stroke|style)="[^"]*#[0-9a-fA-F]{3,8}', index)


def test_jetons_de_couleur_utilises_existent(palettes: dict[str, dict[str, str]]) -> None:
    used = set()
    for path in [*CSS.glob("*.css"), STATIC / "index.html", *STATIC.glob("js/*.js")]:
        used |= set(re.findall(r"var\(--color-([a-z0-9-]+)", path.read_text(encoding="utf-8")))
    assert used <= palettes["sombre"].keys()
