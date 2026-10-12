# Security

## Threat model

The device is an intrusion alarm, so its security goals are:

1. Detection and the local siren must keep working when the network is down or under attack.
2. Nobody on the network may switch the alarm off.
3. Cutting the power must not leave the house disarmed.
4. Alerts should not reveal to outsiders when the house is empty.

| Threat | Default build (demo) | With `secrets.h`, TLS and login |
|---|---|---|
| Remote disarm by anyone who learns the topic | Prevented: remote `DISARM` is refused | Optional, and only compiles with TLS and a broker login |
| Wi-Fi jammed or router switched off | Local alarm continues; events queued (16) and sent on reconnect; broker publishes the Last Will `offline` | Same |
| Power cut or reset while armed | Armed state restored from NVS; door found open starts the entry delay | Same |
| Firmware hang | Task watchdog resets the device; boot event reports the reason | Same |
| Eavesdropping on events (house empty?) | Possible: public broker, no encryption | Encrypted (TLS 8883); private broker |
| Forged commands or events | `ARM` and `STATUS` accepted from anyone | Only clients with broker credentials; use per-topic ACLs on the broker |
| Credentials leaked through the repository | No credentials in the source; `secrets.h` is git-ignored | Same |

## Not yet covered

- No signed over-the-air updates and no secure boot or flash encryption.
- No tamper switch on the enclosure and no battery backup.
- Commands carry no nonce or signature; with TLS and ACLs this relies on the broker for authentication.
- MQTT publishing is at most once (PubSubClient); the queue covers outages, not loss in transit.

These are tracked as future work in the README.

## Reporting a vulnerability

Please open a GitHub issue with the label `security`, or contact the author through the profile page. Do not include working credentials in the report.
