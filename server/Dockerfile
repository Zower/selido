FROM node:15.12.0-alpine3.10

WORKDIR /home/node/

COPY src/ src/
COPY package.json .

RUN npm install

RUN apk add --update openssl

USER node

RUN mkdir /home/node/certs/

ENTRYPOINT [ "sh"]