FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json .

# Simple npm install (NO ci problems)
RUN npm install

# Copy app
COPY . .

EXPOSE 3000

# Dev server with host binding
CMD ["npx", "next", "dev", "--hostname", "0.0.0.0", "--port", "3000"]
