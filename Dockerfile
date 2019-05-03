FROM ubuntu:19.04

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		git \
		python3 \
		python3-dev \
		python3-pip \
		python3-setuptools \
		python3-wheel \
		jq

ADD requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

ADD course-emails.py /usr/local/bin/
ADD save-course-emails.sh /usr/local/bin/

CMD ["/usr/local/bin/save-course-emails.sh"]
