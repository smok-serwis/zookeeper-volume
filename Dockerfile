FROM python:3.8 AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends libboost-filesystem-dev libfuse-dev libzookeeper-mt-dev libbsd-dev

RUN git clone https://github.com/smok-serwis/zookeeper-fuse.git

WORKDIR /zookeeper-fuse
RUN autoreconf -fi && \
    ./configure && \
    make -j4

FROM python:3.8 AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends libzookeeper-mt2 fuse libfuse2 \
                                               libboost-filesystem1.67.0 libbsd0 && \
    apt-get clean

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && \
    rm -rf /tmp/requirements.txt

WORKDIR /app
ADD zookeeper_plugin /app/zookeeper_plugin

COPY --from=builder --chown=ugo+x /zookeeper-fuse/zookeeperfuse /usr/bin/zookeeperfuse

RUN mkdir -p /state /mnt/volumes /run/docker/plugins
