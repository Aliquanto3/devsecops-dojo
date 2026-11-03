# Journal des changements

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
  sans le sous-dossier `app/` (réinstallé). L'ancien dossier n'est jamais modifié ni supprimé ; un
  échec de copie n'empêche pas le démarrage (avertissement, dossier neuf).
