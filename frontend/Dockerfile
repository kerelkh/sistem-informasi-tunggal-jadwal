# --- Build stage ---
FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Note: PUBLIC_SITE_* and API_BASE use $env/dynamic/*, read at request time —
# no build-time ARGs needed. They're supplied as normal env vars at `docker run`/compose time.

# --- Runtime stage ---
FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

COPY --from=build /app/build ./build
COPY --from=build /app/package.json /app/package-lock.json ./
RUN npm ci --omit=dev

EXPOSE 3000

CMD ["node", "build/index.js"]
