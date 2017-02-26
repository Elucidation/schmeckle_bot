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


# Copy code over
COPY . /sb/

WORKDIR /sb

# Run schmecklebot by default
CMD ["/sb/run_sb.sh"]