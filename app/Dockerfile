FROM python:3.11
RUN mkdir /app
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY ./linkedmusic_search /app/linkedmusic_search
EXPOSE 5000
WORKDIR /app/linkedmusic_search
CMD ["flask", "run", "--debug", "--host=0.0.0.0"]
