FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app.py github_dispatch.py ./

CMD ["python", "app.py"]
