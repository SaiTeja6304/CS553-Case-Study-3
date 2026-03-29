FROM python:3.13.5-slim

RUN apt-get update && apt-get install -y && rm -rf /var/lib/apt/lists/*

RUN pip install -r ../requirements.txt --no-cache-dir

WORKDIR /app

COPY ../src/ /app/src/

EXPOSE 22011
EXPOSE 9090

CMD ["streamlit", "run", "src/streamlit_app.py", "--server.port", "22011", "--server.address", "0.0.0.0"]