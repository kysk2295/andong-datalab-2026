FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY index.html ./
COPY src ./src
COPY public ./public
COPY scripts/compress-data.mjs ./scripts/compress-data.mjs
COPY scripts/compress-assets.mjs ./scripts/compress-assets.mjs
RUN npm run build
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/dist ./dist
COPY server.mjs ./
USER node
EXPOSE 8080
CMD ["node", "server.mjs"]
