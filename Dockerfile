FROM python:rc

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
ENV DISCORD_TOK=$DISCORD_TOK

CMD ["python3", "ciel.py"]
