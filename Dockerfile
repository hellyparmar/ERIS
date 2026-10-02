# ERIS - single image: builds the React app, then serves it together with the FastAPI backend.
#   docker build -t eris .  &&  docker run -p 8000:8000 -v eris-data:/app/api/data eris
FROM node:20-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app/api
COPY api/requirements.txt ./
RUN pip install -r requirements.txt
COPY api/ ./
COPY docs/knowledge /app/docs/knowledge
COPY --from=web /web/dist /app/web/dist
RUN useradd --create-home eris && mkdir -p /app/api/data && chown -R eris /app
USER eris
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
