FROM docker.io/node:20-bookworm-slim

WORKDIR /app

COPY ./package.json ./

RUN npm install && npm cache clean --force

ENV PATH ./node_modules/.bin/:$PATH
