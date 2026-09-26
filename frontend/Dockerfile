# Stage 1: Development
FROM node:22-alpine AS dev

WORKDIR /app

RUN chown node:node /app && \
    npm install -g npm@latest --ignore-scripts

USER node

COPY --chown=node:node package*.json .npmrc* ./

RUN npm ci --legacy-peer-deps

# Copy specific source directories and config files explicitly
COPY --chown=node:node src/ ./src
COPY --chown=node:node index.html vite.config.ts tsconfig*.json ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]


# Stage 2: Build static assets
FROM dev AS build
RUN npm run build


# Stage 3: Production (Unprivileged Nginx)
FROM nginxinc/nginx-unprivileged:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]