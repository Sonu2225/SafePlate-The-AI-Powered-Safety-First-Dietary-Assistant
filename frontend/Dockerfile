# Use Node.js image
FROM node:22-alpine

WORKDIR /app

# Install dependencies first (caching layer)
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend code
COPY . .

# Expose the Vite port
EXPOSE 5173

# Run the dev server, forcing it to expose to the network
CMD ["npm", "run", "dev", "--", "--host"]