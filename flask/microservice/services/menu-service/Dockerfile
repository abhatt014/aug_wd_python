# Build context is flask/microservice/ so the shared common/ package can be copied in.
FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/menu-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --system app
COPY common/ common/
COPY services/menu-service/app.py .
USER app
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
