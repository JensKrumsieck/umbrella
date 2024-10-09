# Umbrella

A small and simple service for coverage badges working with public repos the service host has access to via GitHub Token Authentification.

It looks for an artifact created by a workflow called `coverage.yml`. The artifact must contain a xml file called `cobertura.xml` which may be created using `cargo tarpaulin`.

The Endpoint returns an image in typical badge format.

## Demo:
![](https://coverage.jenskrumsieck.de/coverage/fairagro/m4.4_sciwin_client?branch=feature%2Fcoverage)