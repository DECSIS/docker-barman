FROM postgres:9.6

RUN apt-get update && \
	apt-get install -y wget openssh-server rsync && \
	rm -rf /var/lib/apt/lists/* && \
	apt-get clean

ENV DOCKERIZE_VERSION v0.5.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN echo 'root:changeme' |chpasswd

RUN sed -ri 's/^PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config	

RUN mkdir -p /var/run/sshd
RUN mkdir -p ~/.ssh/
# The following allows to maintain defined environment in SSH connections
RUN env > /etc/default/locale
RUN echo "export PATH=$PATH" > ~/.bashrc

EXPOSE 22

COPY scripts/docker_entrypoint.sh /docker_entrypoint_rec.sh

ENTRYPOINT ["/docker_entrypoint_rec.sh"]

CMD ["sshd"]