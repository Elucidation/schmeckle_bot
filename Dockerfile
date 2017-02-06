FROM phusion/baseimage:latest
MAINTAINER Sam <elucidation@gmail.com>

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

# Install python and pip and use pip to install the python reddit api PRAW
RUN apt-get -y update && apt-get install -y \
  python \
  python-pip \
   && apt-get clean
RUN pip install --upgrade praw

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY . /tmp/sb/
# Once the docker instance is up, copy over your praw.ini file for credentials
# into /tmp/sb
# Then manually start the script from inside in headless mode using:
# <machine>$ docker exec -it <container> /bin/bash
# <docker>$ cd /tmp/sb
# <docker>$ nohup python -u schmeckle_bot.py > out.log 2> out_error.log &
