FROM python:3

WORKDIR /ciel

RUN pip install -U pip setuptools wheel
RUN pip install pdm

COPY pyproject.toml pdm.lock ./
COPY src/ src/

RUN pdm install --prod --no-editable

CMD ["pdm", "run", "python", "-m", "ciel"]
