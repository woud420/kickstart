FROM oven/bun:{{ bun_version }} AS deps
WORKDIR /app
COPY package.json bun.lock* bunfig.toml* ./
RUN bun install

FROM deps AS build
COPY tsconfig.json tsconfig.build.json ./
COPY src ./src
RUN bun run build

FROM oven/bun:{{ bun_version }} AS runtime
ENV NODE_ENV=production
WORKDIR /app
COPY package.json bun.lock* bunfig.toml* ./
RUN bun install --production
COPY --from=build /app/dist ./dist
USER bun
EXPOSE 8080
CMD ["bun", "dist/main.js"]
