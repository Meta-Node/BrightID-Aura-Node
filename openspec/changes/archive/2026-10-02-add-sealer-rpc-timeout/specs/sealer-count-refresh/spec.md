## Purpose

The receiver reads the IDChain sealer count to decide how many blocks deep a
block must be before it is applied. This capability covers how that read
behaves when the RPC endpoint does not answer.

## ADDED Requirements

### Requirement: Sealer count read is time-bounded
When reading the sealer count, the receiver SHALL give up on a connection
attempt to the IDChain RPC endpoint that has not succeeded within 10 seconds,
and SHALL give up on the read once the endpoint has sent nothing for 10 seconds.
It SHALL treat either like any other failed read: log it and continue. The read
as a whole has no deadline.

#### Scenario: Endpoint stops answering mid-run
- **WHEN** the receiver refreshes the sealer count and the endpoint accepts the
  connection but never responds
- **THEN** the receiver logs the failure after about 10 seconds, keeps the sealer
  count it already has, and continues applying blocks

#### Scenario: Endpoint does not answer at startup
- **WHEN** no sealer count has been read yet and the endpoint never responds
- **THEN** the receiver logs the failure and retries, and does not begin
  applying blocks until a read succeeds
