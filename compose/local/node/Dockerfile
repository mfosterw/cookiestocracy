FROM docker.io/node:20-bookworm-slim

RUN apt-get update && apt-get install --no-install-recommends -y \
    # For healthcheck
    curl

WORKDIR /app/democrasite-frontend

COPY ./democrasite-frontend/package.json .

RUN npm install && npm cache clean --force

ENV PATH ./node_modules/.bin/:$PATH
