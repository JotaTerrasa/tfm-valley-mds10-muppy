# Frontend (Vite dev server). Para producción usar build + nginx.
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

# El navegador del usuario llama al backend en localhost:8000 (mismo host)
ENV VITE_API_URL=http://localhost:8000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
