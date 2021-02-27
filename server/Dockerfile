FROM node:15.10.0

WORKDIR /home/node/

COPY src/* src/
COPY package.json .

RUN npm install

USER node

ENTRYPOINT [ "npm", "start" ]