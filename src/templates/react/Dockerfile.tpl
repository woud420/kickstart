FROM oven/bun:{{ bun_version }} AS deps
WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install

FROM deps AS build
COPY . .
RUN bun run build

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
