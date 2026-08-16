# Builder image for scripts/build-foxx.sh.
#
# Uses the same ArangoDB version and Alpine/musl runtime as db/Dockerfile
# (what matters for native module compatibility: keccak, secp256k1), but a
# modern Node base so foxx-cli's own toolchain runs. The container's system
# Node is only used to drive foxx-cli as an admin tool here - it never
# executes the Foxx service code, which runs inside arangod's embedded V8.
#
# db/Dockerfile currently fails to build from scratch on its own: alpine 3.14
# ships Node 14, but yarn resolves foxx-cli's transitive dependency
# @inquirer/external-editor, which now requires Node >=18. That's a
# pre-existing issue unrelated to this build script.
FROM node:20-alpine

ENV ARANGO_VERSION=3.9.1
ENV ARANGO_URL=https://download.arangodb.com/arangodb39/DEBIAN/amd64
ENV ARANGO_PACKAGE=arangodb3_${ARANGO_VERSION}-1_amd64.deb
ENV ARANGO_PACKAGE_URL=${ARANGO_URL}/${ARANGO_PACKAGE}
ENV ARANGO_SIGNATURE_URL=${ARANGO_PACKAGE_URL}.asc

RUN apk add --no-cache gnupg pwgen binutils numactl numactl-tools zip && \
    npm install -g foxx-cli@2.1.1 && \
    gpg --batch --keyserver keys.openpgp.org --recv-keys CD8CB0F1E0AD5B52E93F41E7EA93F5E56E751E9B && \
    cd /tmp && \
    wget ${ARANGO_SIGNATURE_URL} && \
    wget ${ARANGO_PACKAGE_URL} && \
    gpg --verify ${ARANGO_PACKAGE}.asc && \
    ar x ${ARANGO_PACKAGE} data.tar.gz && \
    tar -C / -x -z -f data.tar.gz && \
    sed -ri \
        -e 's!^(file\s*=\s*).*!\1 -!' \
        -e 's!^\s*uid\s*=.*!!' \
        /etc/arangodb3/arangod.conf && \
    rm -f ${ARANGO_PACKAGE}* data.tar.gz && \
    apk del gnupg
