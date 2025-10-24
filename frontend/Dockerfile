# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --silent
COPY ./src ./src
COPY ./public ./public
RUN npm run build

# Production image with nginx
FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html
# remove default config and add a basic one that serves index.html for SPA
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
