# Journal des changements

## 0.2.1

### Changé : charte générique v2.1

- **Interface à la charte v2.1** (`Aliquanto3/charte-generique`) : jetons de `tokens.css` pris par usage
  dans les rôles de la charte, sombre d'abord (`:root`), clair selon le système ou `data-theme="light"`,
  `data-theme="dark"` force le sombre. Aucune couleur en dur hors de `tokens.css`.
- **Bouton principal neutre** (`--color-button`, `--color-on-button`), bouton secondaire en contour
  `--color-line-strong`, anneau de focus `--color-focus`, filet or sous le titre de page, ombres dures
  remplacées par le halo doux.
- **Polices** : Sora 600 pour les titres (à la place de Fredoka, retirée), Atkinson Hyperlegible pour le
  texte, JetBrains Mono pour le code. Le rapport HTML exporté suit la même palette et embarque Sora.
- **Favicon et pictogramme** de la charte. Captures dans `docs/media/charte-v2/`.
- Tests : contraste WCAG dans les deux thèmes sur une liste explicite de couples (`tests/test_charte.py`),
  aucun hex hors des jetons, aucun aplat bleu de bouton.

## 0.2.0

### Changé : nouveau nom, nouvelle charte

- **Nouveau nom** : le dépôt anciennement `wavedevsecops` (« WaveDevSecOps ») devient `devsecops-dojo`
  (« DevSecOps Dojo »). Le paquet Python devient `devsecops_dojo` et la commande `devsecops-dojo`
  (`uv run devsecops-dojo`). Les anciens liens GitHub (`Aliquanto3/wavedevsecops`, y compris
  `raw.githubusercontent.com` et les archives) sont redirigés par GitHub vers le nouveau dépôt.
- **Charte générique** : palette bleu pétrole et orange brûlé (thèmes clair et sombre, contrastes WCAG AA
  recalculés par les tests), polices libres déjà embarquées (Atkinson Hyperlegible, Fredoka,
  JetBrains Mono), pictogramme et favicon SVG neufs. Nouveaux jetons : `--color-on-status` (texte sur
  un aplat d'erreur) et `--color-success-soft` (fond de succès, à la place de `--color-accent-soft`).
- **Variables d'environnement** : le préfixe `WDS_` devient `DEVSECOPS_DOJO_` (par exemple
  `DEVSECOPS_DOJO_DATA_DIR`, `DEVSECOPS_DOJO_INSTALL_REF`). Les anciennes variables `WDS_*` restent lues
  quand la nouvelle est absente, avec un avertissement (`FutureWarning`, ou message sur stderr pour
  les installeurs).
- **Dossier de données** : `WaveDevSecOps` devient `DevSecOpsDojo` (`%LOCALAPPDATA%\DevSecOpsDojo`,
  `~/Library/Application Support/DevSecOpsDojo`, `~/.local/share/DevSecOpsDojo`). Au premier lancement
  (application ou installeur), l'ancien dossier est copié vers le nouveau s'il n'existe pas encore,
  sans le sous-dossier `app/` (réinstallé), le verrou `app.lock` ni les environnements Python des
  exercices : ceux-ci sont recréés hors ligne au premier usage (outil, commit gardé, run).
  L'ancien dossier n'est jamais modifié ni supprimé ; un échec de copie n'empêche pas le démarrage (avertissement, dossier neuf).
  Une variable `DEVSECOPS_DOJO_*` vide vaut absente : l'ancienne variable sert alors de repli.
- **Espaces copiés** : les balises du pipeline deviennent `dojo:job` / `dojo:end` (l'ancienne forme
  `wds:job` / `wds:end` reste lue), les hooks git posés avant le renommage sont réécrits au
  premier `git commit` ou `git push`, et la garde réseau des anciens environnements d'exercice
  reste active. Le cookie de session devient `devsecops_dojo_session` (sans effet : la session
  change à chaque lancement).
