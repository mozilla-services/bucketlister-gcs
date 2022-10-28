FROM python:3
ADD *.py *.pyc /bucketlister/
ADD templates/listing.html /bucketlister/templates/
ADD requirements.txt /bucketlister/
WORKDIR /bucketlister
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "-k", "gthread", "--threads", "4", "main:app"]
