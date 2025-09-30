FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create directories for uploads and outputs
RUN mkdir -p uploads outputs public

# Expose port
EXPOSE 3001

# Start the server
CMD ["node", "server.js"]