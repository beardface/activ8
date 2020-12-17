FROM arm32v6/node:15.4.0-alpine3.10

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm install

COPY . .

ENV MONGO_HOST "host.docker.internal"
ENV PORT 80

EXPOSE 80

CMD [ "node", "server.js" ]