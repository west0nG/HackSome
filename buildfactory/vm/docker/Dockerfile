# Foundagent VM layer — minimal cua-ubuntu image with deterministic, fast boot.
#
# Based on trycua/cua-ubuntu (Kasm + Ubuntu 22.04 XFCE + Firefox + bundled cua
# computer-server). The only change: replace the upstream startup script, which
# does a heavy multi-GB `cua-agent[all]` pip upgrade on every boot, with a direct
# launch of the already-bundled computer-server. See custom_startup.sh for why.
FROM trycua/cua-ubuntu:latest

COPY --chmod=0755 custom_startup.sh /dockerstartup/custom_startup.sh
