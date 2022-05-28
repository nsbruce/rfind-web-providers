# RFInd Web data provider Python package

This repository contains a python package to provide data for the [rfind-web](https://github.com/nsbruce/rfind-web) stack.

## Installation

This project has been built with [poetry](https://python-poetry.org/) v1.2.0b1, so you can install it with a simple `poetry install`. I have not tested it on other platforms or older poetry versions.

The first thing needed is to generate an environment file to contain variables for your particular data provider. The `poetry run generate-env` command will generate a .env file in the root of the project. You should then copy this with `cp .env .env.local` and make appropriate changes. This workflow prevents you from manually editing the .env file and later overwriting it with defaults by re-running the `generate-env` script. If the default .env changes, you will need to manually update your .env.local file.

## Running the data provider

There are three data providers included in this package, each is described briefly below.

### Simulation

The simulation data provider uses a rudimentary spectra generator. So far it allows you to add single tone carriers and FM signals to a paramterized noise floor. The signals and noise floor will obey the `SPECTRA_MAX_VALUE` and `SPECTRA_MIN_VALUE` parameters in the generated .env.local file. To run the simulation without changing parameters use `poetry run sim`. If you want to adjust the signals in use, you can do something like

```python
from rfind_web.providers import DataProviderSim
provider = DataProviderSim()
provider.fcs = [150e6, 1.1e9]
provider.fms = [(1.1e9, 0.1e9), (1.2e9, 0.2e9)]
provider.sigma = 0.5
provider.run()
```

## Contributing

This package is mypy and flake8 compliant. Before issuing a PR, please lint with `poetry run poe lint`.

The package is also formatted with isort and black. Before issuing a PR, please format with `poetry run poe format`.

Although maybe contentious, I have committed the .vscode folder with my [settings.json](.vscode/settings.json) file. If you are using vscode this should make linting "on the go" easier.
