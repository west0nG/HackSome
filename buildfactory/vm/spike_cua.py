"""VM-layer spike: start a cua-ubuntu container via the SDK and verify computer-server.

Validates VM-layer PRD AC1 (isolated container + Computer Use) minimally:
  - SDK launches the container with correct env (VNC_PW, -disableBasicAuth) and
    port maps (6901 VNC, 8000 computer-server).
  - Connect to computer-server, read screen size, capture a screenshot.

Run: .venv-cua/bin/python vm/spike_cua.py
"""

import asyncio
import os
import traceback

from computer import Computer

OUT = "/Users/weston/dev/BuildFactory/vm/shot.png"


async def main():
    c = Computer(
        os_type="linux",
        provider_type="docker",
        image=os.environ.get("CUA_IMAGE", "foundagent/cua-ubuntu:latest"),
        name="founder-01",
    )
    await c.run()
    print("RUN OK: container started")

    try:
        size = await c.interface.get_screen_size()
        print("screen size:", size)
    except Exception as e:
        print("get_screen_size failed:", repr(e))

    img = await c.interface.screenshot()
    data = img if isinstance(img, (bytes, bytearray)) else bytes(img)
    with open(OUT, "wb") as f:
        f.write(data)
    print(f"SCREENSHOT OK: {len(data)} bytes -> {OUT}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
