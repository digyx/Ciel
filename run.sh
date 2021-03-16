git pull
docker kill ciel
docker container rm ciel
docker build -t ciel .
docker run -d --name ciel -e DISCORD_TOK ciel