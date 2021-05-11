FROM python:3.8 AS builder

RUN git clone https://github.com/borowskk/zookeeper-fuse.git && \
    apt-get update && \
    apt-get install -y libboost1.67-all-dev libfuse-dev libzookeeper-mt-dev

WORKDIR /zookeeper-fuse
RUN autoreconf -fi && \
    ./configure && \
    make -j4

FROM python:3.8 AS runtime

RUN apt-get update && \
    apt-get install -y libzookeeper-mt2 fuse libfuse2 libboost1.67-all-dev && \
    apt-get clean

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && \
    rm -rf /tmp/requirements.txt

WORKDIR /app
ADD zookeeper_plugin /app/zookeeper_plugin
ADD run.sh /run.sh

COPY --from=builder /zookeeper-fuse/zookeeperfuse /usr/bin/zookeeperfuse

RUN chmod ugo+x /run.sh /usr/bin/zookeeperfuse && \
    mkdir -p /state /mnt/volumes /run/docker/plugins

CMD ["/usr/local/bin/gunicorn", "-w", "1", "--threads", "4", "--bind", \
     "unix:/run/docker/plugins/zookeeper-volume.sock", "zookeeper_plugin.run:app"]
