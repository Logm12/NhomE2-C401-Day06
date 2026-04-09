FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund

FROM node:20-alpine AS builder
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Tránh chạy migrate trong build để không phụ thuộc DB
RUN npx next build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY package.json ./
COPY next.config.js ./
COPY .env.example ./.env.example
COPY lib ./lib
COPY app ./app
COPY components ./components
COPY styles ./styles
CMD ["npx", "next", "start"]
