FROM python:3.7

WORKDIR /app

COPY app .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 1337
EXPOSE 666

CMD ["python", "-u", "server.py"]