FROM python:3.10 AS builder

RUN pip install -U pip setuptools wheel
RUN pip install pdm

WORKDIR /ciel
COPY pyproject.toml pdm.lock ./
COPY src/ src/

RUN pdm install --prod --no-editable --no-lock

# Dist
FROM python:3.10-alpine

ENV PYTHONPATH=/project/pkgs
COPY --from=builder /ciel/.venv/lib/python3.10/site-packages /project/pkgs

CMD ["python", "-m", "ciel"]
