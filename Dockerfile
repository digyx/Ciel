FROM python:3

WORKDIR /usr/src/app

RUN pip install -U pip setuptools wheel
RUN pip install pdm

COPY pyproject.toml pdm.lock ./
COPY src/ src/

RUN pdm install --prod --no-editable

CMD ["pdm", "run", "python", "-m", "ciel"]
