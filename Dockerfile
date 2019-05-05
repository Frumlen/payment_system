### Build and install packages
FROM python:3.7 as build-python
ADD . /opt/payment_system
WORKDIR /opt/payment_system
RUN pip3 install -r requirements.txt
CMD ["/bin/sh", "./run.sh"]