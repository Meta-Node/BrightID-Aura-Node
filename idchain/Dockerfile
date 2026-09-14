# IDChain sync node — multi-stage build
# Source: https://github.com/IDChain-eth/IDChain, tag idc1.9.18 (Geth 1.9 fork, go.mod says go1.13)
# Go toolchain pinned to golang:1.14-alpine, matching the tag's own build recipe (DAppNodePackage-IDChain).
FROM golang:1.14-alpine AS builder
RUN apk add --no-cache make gcc musl-dev linux-headers git
RUN git clone --branch idc1.9.18 --depth 1 https://github.com/IDChain-eth/IDChain.git /go/IDChain
WORKDIR /go/IDChain
RUN make geth

FROM alpine:latest
RUN apk add --no-cache ca-certificates libstdc++ eudev-libs libgcc bash
COPY --from=builder /go/IDChain/build/bin/geth /usr/local/bin/geth
ENTRYPOINT ["geth"]
