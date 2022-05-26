# RFInd Web data provider Python package

This repository contains a python package to provide data for the [rfind-web](https://github.com/nsbruce/rfind-web) stack.

## Installation

This project has been built with [poetry](https://python-poetry.org/) v1.2.0b1, so you can install it with a simple `poetry install`. I have not tested it on other platforms or older poetry versions.

The first thing needed is to generate an environment file to contain variables for your particular data provider. The `poetry run generate-env` command will generate a .env file in the root of the project. You should then copy this with `cp .env .env.local` and make appropriate changes. This workflow prevents you from manually editing the .env file and later overwriting it with defaults by re-running the `generate-env` script. If the default .env changes, you will need to manually update your .env.local file.

## Contributing

This package is mypy and flake8 compliant. Before issuing a PR, please lint with `poetry run poe lint`.

The package is also formatted with isort and black. Before issuing a PR, please format with `poetry run poe format`.

Although maybe contentious, I have committed the .vscode folder with my [settings.json](.vscode/settings.json) file. If you are using vscode this should make linting "on the go" easier.
