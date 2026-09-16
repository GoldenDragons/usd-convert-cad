# Contributing

<!-- SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->

Thank you for your interest in `usd-convert-cad`.

This repository contains documentation and the NVIDIA Agent Skill for the
Omniverse CAD Converter. The converter is distributed separately through the
`usd-convert-cad` Python wheel.

## Contribution Policy

This project is not currently accepting external contributions or pull requests.
Unsolicited pull requests will be closed. Because external contributions are not
accepted, no Contributor License Agreement (CLA) or Developer Certificate of
Origin (DCO) process applies.

NVIDIA maintainers may continue to update this repository through NVIDIA's
internal development and review processes. A future change to the external
contribution policy will be documented in this file and in `README.md`.

## Reporting Issues

Use GitHub issues for documentation problems, skill behavior, and supported-format
requests. Include enough detail for maintainers to reproduce or understand the
issue:

- Repository commit.
- Operating system and Python version. Python 3.12 is required by the wheel.
- Installed `usd-convert-cad` wheel version (`python -c "import usd_convert_cad; print(usd_convert_cad.__version__)"`).
- Input CAD format and requested output format.
- Exact command used and the converter's stdout/stderr.

Do not report security vulnerabilities through public GitHub issues. See
`SECURITY.md` for private disclosure instructions.

## Agent Skill Directories

`skills/omniverse-cad-to-usd/SKILL.md` is the single source of truth. The
`.agent`, `.cursor`, `.claude`, and `.codex` directories are symbolic links to
`skills`, so editing the canonical file updates every agent's view automatically.
Do not replace these links with real directories or copies.

On platforms that cannot create symlinks (for example Windows without Developer
Mode), Git still records them as symlinks; enable Developer Mode or run with
privileges and `git checkout -- .agent .cursor .claude .codex` to materialize
them locally.

## Repository Conventions

- `skills/omniverse-cad-to-usd/SKILL.md` is the canonical NVIDIA Agent Skill
  entrypoint. Keep the directory name aligned with the `name` frontmatter.
- The supported-format table is documentation that mirrors the formats supported
  by the installed wheel. Keep it accurate against `usd-convert-cad --help` and
  the wheel's documentation.

## Coding Guidelines

- Follow the existing style in the files you edit.
- Keep changes narrowly scoped and avoid unrelated formatting churn.
- Preserve the SPDX header used by existing files.

## License

The agent skill is licensed under the Apache License, Version 2.0 and the
Creative Commons Attribution 4.0 International Public License. See
`skills/omniverse-cad-to-usd/LICENSE.md` for details. The Omniverse CAD Converter
package and runtime are governed by the NVIDIA terms in `LICENSE.md`.
