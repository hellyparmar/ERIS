# ERIS - single image: builds the React app, then serves it together with the FastAPI backend.
#   docker build -t eris .  &&  docker run -p 8000:8000 -v eris-data:/app/api/data eris
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app/api
COPY api/requirements.txt api/constraints.txt ./
RUN pip install -r requirements.txt -c constraints.txt
COPY api/ ./
COPY docs/knowledge /app/docs/knowledge
# The demo database is prepared here, on the build machine: synthetic data, a few genuine user operations,
# pre-computed forecasts and page answers. A small hosted instance (e.g. Render's free plan) then starts with
# everything ready instead of spending ~10 minutes generating it after every wake-up. --build-arg BAKE_DEMO=0
# builds an image with an empty database instead (start with SEED_DEMO_DATA=false or your own DATABASE_URL).
ARG BAKE_DEMO=1
RUN mkdir -p /app/api/data && if [ "$BAKE_DEMO" = "1" ]; then python -m app.seed.bake; fi
COPY --from=web /web/dist /app/web/dist
RUN useradd --create-home eris && chown -R eris /app
USER eris
EXPOSE 8000
ENV PORT=8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/health')"
# hosting platforms (Render, Fly.io, Railway) pass the port to listen on in $PORT
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
