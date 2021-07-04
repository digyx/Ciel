# Update repo
git pull

# Cleanup up container
docker kill ciel
docker container rm ciel

# Build & start new container
mkdir data || true
docker build -t ciel .
docker run -d --name ciel -e DISCORD_TOK -v $PWD/data:/usr/src/app/data ciel
