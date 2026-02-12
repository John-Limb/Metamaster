# Stage 1: Build stage
FROM node:25.6.0-alpine AS builder

WORKDIR /app

# Set environment variables
ENV VITE_APP_NAME=MetaMaster
ENV VITE_APP_VERSION=1.0.0

# Install dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Verify build output
RUN test -d dist && ls -la dist/ && echo "Build completed successfully"

# Stage 2: Runtime with nginx only
FROM alpine:latest

# Install nginx and curl for healthchecks
RUN apk add --no-cache nginx curl

# Copy nginx configuration from builder
COPY --from=builder /app/nginx.conf /etc/nginx/nginx.conf

# Create necessary directories
RUN mkdir -p /var/cache/nginx /var/run/nginx /var/www/html

# Copy built application from builder stage
COPY --from=builder /app/dist /var/www/html

# Verify files were copied
RUN test -f /var/www/html/index.html && ls -la /var/www/html/ && echo "Frontend artifacts deployed successfully" || (echo "ERROR: index.html not found" && exit 1)

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
