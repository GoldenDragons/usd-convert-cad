# Changelog

<!-- SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->


## [0.3.0] - 2026-09-09
### Added
- Added `--read-constraints` to export CATIA V5, NX, and SolidWorks `Fix`, CATIA V5 `Fix Together`, NX `Bond`, and SolidWorks `Lock` mate assembly constraints as USD Physics fixed joints.
- Added `.usdz` (USDZ) export support to the CLI.
- Added `--material-type preview-surface-materialx` for OpenPBR MaterialX output with a USD Preview Surface fallback.
- Documented 2D CAD linework conversion via `--convert-curves`, including DWG/DXF model-space limitations in `LIMITATIONS.md`.

### Changed
- Updated the HOOPS Exchange SDK from 2026.5.0 to 2026.7.0.
- Updated the OpenUSD Exchange SDK from 2.3 to 3.0.
- Added display-color primvars alongside explicit materials.
- Added a root-bound `DefaultDisplayColorMaterial` when generated materials are disabled.
- Improved normal-source diagnostic messages.

## [0.2.0] - 2026-07-01
### Added
- Documented and exposed the `--revit-lod <0-3>` CLI option for selecting Revit detail level.

### Changed
- Removed the Omniverse Kit workflow. Conversion is no longer performed by installing `omniverse-kit` and pulling a CAD converter extension from the Kit registry.
- Converted this repository into a pure skill repository. The agent skill now instructs agents to install and drive the self-contained `usd-convert-cad` Python wheel published to PyPI.

### Removed
- `install.py`, `validate.py`, `convert.py`, `_script_utils.py`, the `app/` and `setup/` scripts, the `src/usd_convert_cad/` Python package, and `pyproject.toml`. Conversion now lives entirely in the published wheel.

## [0.1.1] - 2026-05-20
- Updates to address NSPECT review

## [0.1.0] - 2026-05-14
### Added
- Initial development version
