FROM node:24-alpine AS build
WORKDIR /workspace
COPY package.json package-lock.json tsconfig.base.json eslint.config.mjs ./
COPY packages/contracts ./packages/contracts
COPY frontend/react ./frontend/react
COPY apps/demo-web ./apps/demo-web
RUN npm ci
ARG VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build --workspace @buildable/demo-web

FROM nginx:1.29-alpine
COPY devops/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/demo-web/dist /usr/share/nginx/html
EXPOSE 80

