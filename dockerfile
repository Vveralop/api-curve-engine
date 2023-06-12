FROM python:3.10.9

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENTRYPOINT ["python", "manage.py"]
CMD ["runserver", "0.0.0.0:5000"]