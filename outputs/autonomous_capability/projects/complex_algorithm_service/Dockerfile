FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV XDG_CACHE_HOME=/tmp
COPY pyproject.toml ./
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.1.2"     && python -m pip install --no-cache-dir ".[test]"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
