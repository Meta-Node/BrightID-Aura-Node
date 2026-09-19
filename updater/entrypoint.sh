#!/bin/bash
# make BN_UPDATER_*, BN_ARANGO_* and BN_CONSENSUS_IDCHAIN_RPC_URL env vars available to cronjob
printenv | grep "BN_UPDATER\|BN_ARANGO\|BN_CONSENSUS_IDCHAIN_RPC_URL\|PATH" > /tmp/environment_vars
python -u /code/start.py
