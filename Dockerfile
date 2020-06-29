FROM library/python:buster

LABEL maintainer sburney@sifnt.net.au

COPY . /opt/emberpulse
RUN pip install --no-cache-dir -e /opt/emberpulse

ENV PYTHONUNBUFFERED=1

CMD ["emberpulse-stats"]
