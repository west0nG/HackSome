#!/bin/bash
# Foundagent VM layer — start the bundled cua computer-server directly.
#
# Upstream trycua/cua-ubuntu's custom_startup.sh runs on EVERY boot:
#     sudo uv pip install --upgrade --system cua-computer-server "cua-agent[all]"
#     /usr/bin/python3 -m computer_server
# The `cua-agent[all]` upgrade pulls multi-GB ML deps (torch / cuda / transformers /
# gradio / playwright) that we do NOT need — Claude is the brain, not a local model.
# That download blocks computer-server startup (>100s, network-dependent) and is the
# root cause of "Computer API Server not ready".
#
# The bundled computer-server (0.3.17) already works with the host cua-computer SDK,
# so we skip the upgrade entirely for fast, offline-friendly, deterministic boots.
exec /usr/bin/python3 -m computer_server
