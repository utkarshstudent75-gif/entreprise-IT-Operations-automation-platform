FROM node:22-alpine

WORKDIR /app

RUN chown node:node /app

USER node

COPY --chown=node:node package*.json ./

RUN npm ci

# Copy specific source directories and config files explicitly
COPY --chown=node:node src/ ./src
COPY --chown=node:node index.html vite.config.ts tsconfig*.json ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]