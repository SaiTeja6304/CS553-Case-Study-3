FROM python:3.13.5-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir prometheus-client
RUN apt-get update && apt-get install -y curl

COPY src/ /app/src/

EXPOSE 22012

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "22012"]