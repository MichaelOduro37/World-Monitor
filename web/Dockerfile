# Build stage
FROM node:20-alpine AS build
WORKDIR /app
# Accept the backend API URL at build time (defaults to relative path for VPS/nginx-proxy setups)
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL
COPY package.json .
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
