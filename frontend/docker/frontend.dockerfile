FROM python:3.13.5-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir prometheus-client

COPY src/ /app/src/

EXPOSE 22011
EXPOSE 33333

CMD ["streamlit", "run", "src/streamlit_app.py", "--server.port", "22011", "--server.address", "0.0.0.0"]