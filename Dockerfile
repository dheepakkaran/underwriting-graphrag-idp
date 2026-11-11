FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv export --frozen --no-dev --no-hashes --no-emit-project > req.txt && pip install --no-cache-dir -r req.txt
COPY src ./src
COPY app ./app
COPY prompts ./prompts
COPY data/records.sqlite ./data/records.sqlite
COPY results ./results
# no secrets baked in: ANTHROPIC_API_KEY comes from the environment at run time (compose env_file)
RUN useradd -m app && chown -R app /srv
USER app
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
