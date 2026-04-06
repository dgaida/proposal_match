# Projekt-Metriken

Diese Seite bietet einen Überblick über die Qualität und den Status der Dokumentation sowie des Codes.

## API-Dokumentationsabdeckung

Wir streben eine Abdeckung von **95%** für alle öffentlichen APIs an.

![Interrogate Badge](../assets/interrogate_badge.svg)

- **Status**: Aktiv überwacht durch CI.
- **Werkzeug**: [interrogate](https://interrogate.readthedocs.io/)

## Build-Status

| Metrik | Status |
|--------|--------|
| Dokumentation (MkDocs) | ![Docs Status](https://github.com/dgaida/proposal_match/actions/workflows/docs.yml/badge.svg) |
| Code-Qualität (Ruff) | ![Lint Status](https://github.com/dgaida/proposal_match/actions/workflows/lint.yml/badge.svg) |
| Tests (Pytest) | ![Tests Status](https://github.com/dgaida/proposal_match/actions/workflows/tests.yml/badge.svg) |

## Changelog-Aktualität

Der Changelog wird automatisch bei jedem Release basierend auf [Conventional Commits](https://www.conventionalcommits.org/) generiert.

- **Werkzeug**: [git-cliff](https://git-cliff.org/)
