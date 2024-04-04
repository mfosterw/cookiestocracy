FROM docker.io/node:20-bookworm-slim

WORKDIR /app/democrasite-frontend

COPY ./democrasite-frontend/package.json .

RUN npm install && npm cache clean --force

ENV PATH ./node_modules/.bin/:$PATH
