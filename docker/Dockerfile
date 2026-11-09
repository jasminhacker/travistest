FROM debian:trixie

RUN apt-get update &&\
	apt-get install -y python3-venv inetutils-ping ffmpeg libpq-dev &&\
    apt-get clean &&\
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" DOCKER="1"

RUN pip install --no-cache-dir -U pip

WORKDIR /opt/raveberry

COPY backend/requirements/common.txt backend/requirements/youtube.txt backend/requirements/spotify.txt backend/requirements/prod.txt backend/requirements/docker.txt /opt/raveberry/requirements/

RUN pip install --no-cache-dir -U -r requirements/docker.txt -r requirements/spotify.txt -r requirements/spotify.txt
RUN mkdir logs

# copying multiple directories in one layer is not easily doable
COPY backend/core /opt/raveberry/core
COPY backend/config /opt/raveberry/config
COPY backend/main /opt/raveberry/main
COPY backend/scripts /opt/raveberry/scripts
COPY backend/templates /opt/raveberry/templates
COPY AUTHORS LICENSE backend/manage.py backend/VERSION /opt/raveberry/
COPY docker/entrypoint.sh /entrypoint.sh

COPY docker/pulse-client.conf /etc/pulse/client.conf

# create a user with the UID 1000, so it can access the host's pulse server
# this user needs write access on its config, so add it to the www-data group
RUN mkdir -p /Music/raveberry &&\
	chown -R www-data:www-data /opt/raveberry /Music/raveberry &&\
	useradd -mu 1000 -g 33 pulse_user

EXPOSE 9000

USER www-data

ENTRYPOINT ["/entrypoint.sh"]
CMD ["daphne", "--bind", "0.0.0.0", "--port", "9000", "main.asgi:application"]
