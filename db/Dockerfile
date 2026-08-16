# Edited from https://github.com/arangodb/arangodb-docker/blob/official/alpine/3.9.1/Dockerfile
FROM alpine:3.14
MAINTAINER Frank Celler <info@arangodb.com>

ENV ARANGO_VERSION 3.9.1
ENV ARANGO_NO_AUTH true
ENV ARANGO_URL https://download.arangodb.com/arangodb39/DEBIAN/amd64
ENV ARANGO_PACKAGE arangodb3_${ARANGO_VERSION}-1_amd64.deb
ENV ARANGO_PACKAGE_URL ${ARANGO_URL}/${ARANGO_PACKAGE}
ENV ARANGO_SIGNATURE_URL ${ARANGO_PACKAGE_URL}.asc

# see
#   https://www.arangodb.com/docs/3.9/programs-arangod-server.html#managing-endpoints
#   https://www.arangodb.com/docs/3.9/programs-arangod-log.html

# nodejs/npm come from Alpine 3.18's repos, not 3.14's (this image's base) -
# 3.14 only ships Node 14, too old for foxx-cli's dependency tree, which now
# requires Node >=18. This must run before any other apk package: if an
# older libstdc++/libssl from 3.14's own repo installs first, apk treats
# that as satisfying node's dependency even though the ABI doesn't match,
# and node fails at runtime with "Error relocating /usr/bin/node: symbol
# not found". Installing node/npm first avoids that.
RUN apk add --no-cache --repository=https://dl-cdn.alpinelinux.org/alpine/v3.18/community --repository=https://dl-cdn.alpinelinux.org/alpine/v3.18/main nodejs npm && \
    apk add --no-cache gnupg pwgen binutils numactl numactl-tools && \
    npm install -g foxx-cli@2.1.1 && \
    mv "$(command -v foxx)" /usr/local/bin/foxx-real && \
    gpg --batch --keyserver keys.openpgp.org --recv-keys CD8CB0F1E0AD5B52E93F41E7EA93F5E56E751E9B && \
    mkdir /docker-entrypoint-initdb.d && \
    cd /tmp                                && \
    wget ${ARANGO_SIGNATURE_URL}           && \
    wget ${ARANGO_PACKAGE_URL}             && \
    gpg --verify ${ARANGO_PACKAGE}.asc     && \
    ar x ${ARANGO_PACKAGE} data.tar.gz     && \
    tar -C / -x -z -f data.tar.gz          && \
    sed -ri \
        -e 's!^(file\s*=\s*).*!\1 -!' \
        -e 's!^\s*uid\s*=.*!!' \
        /etc/arangodb3/arangod.conf        && \
    chgrp -R 0 /var/lib/arangodb3 /var/lib/arangodb3-apps && \
    chmod -R 775 /var/lib/arangodb3 /var/lib/arangodb3-apps && \
    rm -f ${ARANGO_PACKAGE}* data.tar.gz && \
    apk del gnupg
# Note that Openshift runs containers by default with a random UID and GID 0.
# We need that the database and apps directory are writable for this config.

ENV GLIBCXX_FORCE_NEW=1
COPY docker-entrypoint.sh /entrypoint.sh
# docker-foxx.sh execs /usr/local/bin/foxx-real (the actual npm-installed
# binary, moved aside above) and must land at the exact path `foxx` resolves
# to via PATH (/usr/local/bin, which comes before /usr/bin on Alpine) so it
# actually intercepts every invocation - including docker-entrypoint.sh's
# bare `foxx` calls - rather than being silently shadowed by the real
# binary. It previously targeted /usr/bin/foxx, which PATH never reaches.
COPY docker-foxx.sh /usr/local/bin/foxx

ENTRYPOINT ["/entrypoint.sh"]

CMD ["arangod"]
