# Project Metrics

This page provides an overview of the quality and status of the documentation and code.

## API Documentation Coverage

We aim for **95%** coverage for all public APIs.

![Interrogate Badge](../../assets/interrogate_badge.svg)

- **Status**: Actively monitored by CI.  
- **Tool**: [interrogate](https://interrogate.readthedocs.io/)  

## Build Status

| Metric | Status |
|--------|--------|
| Documentation (MkDocs) | ![Docs Status](https://github.com/dgaida/proposal_match/actions/workflows/docs.yml/badge.svg) |
| Code Quality (Ruff) | ![Lint Status](https://github.com/dgaida/proposal_match/actions/workflows/lint.yml/badge.svg) |
| Tests (Pytest) | ![Tests Status](https://github.com/dgaida/proposal_match/actions/workflows/tests.yml/badge.svg) |

## Changelog Freshness

The changelog is automatically generated for each release based on [Conventional Commits](https://www.conventionalcommits.org/).

- **Tool**: [git-cliff](https://git-cliff.org/)  
