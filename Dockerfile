FROM python:3.9.7-alpine
COPY ./requirements.txt /app/requirements.txt
RUN apk update
RUN apk add py-pip
RUN apk add --no-cache python3-dev
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt
WORKDIR /app
COPY . /app
CMD ["python3", "WorkoutVis.py"]