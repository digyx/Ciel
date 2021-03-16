# Update repo
git pull

# Cleanup up container
docker kill ciel
docker container rm ciel

# Build & start new container
docker build -t ciel .
docker run -d --name ciel -e DISCORD_TOK ciel