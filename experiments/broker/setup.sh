#!/usr/bin/env bash
# Build a real Mosquitto deployment for the access-control validation: a private CA, a server
# certificate, a password file with three identities, and two ACL variants.
#
# Everything is written under a run directory that is created fresh each time, so the broker
# state cannot leak between runs. Nothing here is committed except this script: the keys are
# throwaway test material generated on demand, and committing them would be committing
# credentials.
set -euo pipefail
cd "$(dirname "$0")"

RUN="${1:-$PWD/run}"
rm -rf "$RUN"
mkdir -p "$RUN"
cd "$RUN"

# ---------------------------------------------------------------- TLS material
# A private CA and a server certificate for localhost. The device in the real system pins a CA
# with setCACert, so a private CA is exactly the right model, not a shortcut.
openssl req -x509 -newkey rsa:2048 -sha256 -days 2 -nodes \
  -keyout ca.key -out ca.crt -subj "/CN=smart-home-test-ca" 2>/dev/null

openssl req -newkey rsa:2048 -sha256 -nodes -keyout server.key -out server.csr \
  -subj "/CN=localhost" 2>/dev/null

cat > server.ext <<'EXT'
subjectAltName = DNS:localhost, IP:127.0.0.1
extendedKeyUsage = serverAuth
EXT

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 2 -sha256 -extfile server.ext 2>/dev/null

# ---------------------------------------------------------------- identities
# Three accounts. The adversary never has an account of its own: it steals one of the others,
# which is the whole point of the credential-compromise scenarios.
#   operator : the controller app or home-automation bridge
#   device   : the ESP32
#   alarm    : the single shared account used by the shared-credential variant
rm -f passwd
mosquitto_passwd -b -c passwd operator operator-secret  2>/dev/null
mosquitto_passwd -b     passwd device   device-secret   2>/dev/null
mosquitto_passwd -b     passwd alarm    alarm-secret    2>/dev/null

# ---------------------------------------------------------------- ACL variants
# Mosquitto denies by default once an acl_file is configured, so every permission below is
# explicit. These are the permissions a competent operator would write, not weakened ones:
# only the controller may publish commands, and the device may only read them.
cat > acl_perclient <<'ACL'
user operator
topic write home/alarm/+/cmd
topic read  home/alarm/+/stat

user device
topic read  home/alarm/+/cmd
topic write home/alarm/+/stat
ACL

# The shared-credential variant. One account is used by both the controller and the device, so
# the ACL must grant it write on the command topic for the system to work at all. This is not a
# misconfigured ACL; it is the best ACL possible given a shared credential.
cat > acl_shared <<'ACL'
user alarm
topic readwrite home/alarm/+/cmd
topic readwrite home/alarm/+/stat
ACL

# ---------------------------------------------------------------- broker configs
for variant in perclient shared; do
  cat > "mosquitto_${variant}.conf" <<CONF
# The packaged broker drops privileges to the mosquitto user, which cannot read a run
# directory created by the experimenter. This is a throwaway test instance bound to loopback,
# so it runs as the invoking user instead of widening permissions on the key material.
user $(id -un)
per_listener_settings true
listener 18883 127.0.0.1
allow_anonymous false
password_file $RUN/passwd
acl_file $RUN/acl_${variant}
cafile $RUN/ca.crt
certfile $RUN/server.crt
keyfile $RUN/server.key
tls_version tlsv1.2
log_dest file $RUN/broker_${variant}.log
log_type all
CONF
done

# The broker warns that world-readable credential and ACL files will be refused by future
# versions. Tighten them now rather than carrying a warning into every log we publish.
chmod 0700 passwd acl_perclient acl_shared

echo "$RUN"
