FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Build will happen at runtime to pick up env vars
# Or during the command phase in docker-compose

EXPOSE 3000

CMD ["npm", "run", "dev"]
