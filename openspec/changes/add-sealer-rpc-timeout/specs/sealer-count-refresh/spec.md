## Purpose

The receiver reads the IDChain sealer count to decide how many blocks deep a
block must be before it is applied. This capability covers how that read
behaves when the RPC endpoint does not answer.

## ADDED Requirements

### Requirement: Sealer count read is time-bounded
The receiver SHALL wait no longer than 10 seconds to connect to the IDChain RPC
endpoint, and no longer than 10 seconds for response data, when reading the
sealer count. It SHALL treat an expired wait like any other failed read: log it
and continue.

#### Scenario: Endpoint stops answering mid-run
- **WHEN** the receiver refreshes the sealer count and the endpoint accepts the
  connection but never responds
- **THEN** the receiver logs the failure after 10 seconds, keeps the sealer
  count it already has, and continues applying blocks

#### Scenario: Endpoint does not answer at startup
- **WHEN** no sealer count has been read yet and the endpoint never responds
- **THEN** the receiver logs the failure and retries, and does not begin
  applying blocks until a read succeeds
