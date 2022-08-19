#!/usr/bin/env just --justfile

test:
    - pdm run pytest --cov
    rm ciel.db

lint:
    pdm run black .
