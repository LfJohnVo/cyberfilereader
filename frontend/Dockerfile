# ---- etapa 1: build ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# VITE_API_URL queda VACÍA a propósito: el frontend usa rutas relativas /api
# y nginx hace el proxy. Cero CORS en producción.
ENV VITE_API_URL=
RUN npm run build

# ---- etapa 2: servir ----
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
