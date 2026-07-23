#!/usr/bin/env python3
"""generate_image.py — image-generation wrapper for the gen-image skill.

Paths:
  PRIMARY : OpenAI Images API (needs OPENAI_API_KEY). Default model
            gpt-image-1-mini (cheapest that is good enough for scouting);
            pass --model gpt-image-2 --quality medium/high for finals.
  SIDE    : Codex CLI built-in image generation (ChatGPT subscription).
            Opt-in via GEN_IMAGE_VIA_CODEX=1. Best-effort: any failure
            falls back to the API path automatically. Slower (1-2 min),
            burns shared subscription quota at 3-5x a normal turn, and the
            CLI contract is not public API — do not make it the only path.

Usage:
  python3 generate_image.py --prompt "..." --out out.png
      [--size 1080x1440] [--model gpt-image-1-mini] [--quality low]
      [--ref path.png] [--timeout 300] [--retries 2]

Notes:
  - Arbitrary --size works: the API is called at the nearest supported size
    (1024x1024 / 1024x1536 / 1536x1024) and the result is resized to the
    exact pixels via sips (macOS) or ImageMagick convert (Linux).
  - --ref (reference image for consistency/edit) is honored on the codex
    path (-i). On the API path it is currently ignored with a warning
    (images/edits multipart deferred).
  - No third-party Python deps. Exit codes: 0 ok, 1 all paths failed,
    2 config error (no key and codex disabled/unavailable).
"""

import argparse
import base64
import glob
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

API_URL = "https://api.openai.com/v1/images/generations"
API_SIZES = {"square": "1024x1024", "portrait": "1024x1536", "landscape": "1536x1024"}
PNG_MAGIC = b"\x89PNG"
JPG_MAGIC = b"\xff\xd8"


def log(msg):
    print(f"[gen-image] {msg}", file=sys.stderr)


def is_image(path):
    try:
        with open(path, "rb") as f:
            head = f.read(4)
        return head.startswith(PNG_MAGIC) or head.startswith(JPG_MAGIC)
    except OSError:
        return False


def nearest_api_size(w, h):
    if w == h:
        return API_SIZES["square"]
    return API_SIZES["portrait"] if h > w else API_SIZES["landscape"]


def resize_exact(path, w, h):
    """Post-process to exact pixels. sips wants HEIGHT first."""
    if platform.system() == "Darwin" and shutil.which("sips"):
        cmd = ["sips", "-z", str(h), str(w), path]
    elif shutil.which("convert"):
        cmd = ["convert", path, "-resize", f"{w}x{h}!", path]
    else:
        log(f"WARN: no sips/convert — leaving native size (wanted {w}x{h})")
        return
    subprocess.run(cmd, check=False, capture_output=True, timeout=60)


def api_generate(prompt, out_path, size, model, quality, timeout, retries):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log("API path unavailable: OPENAI_API_KEY not set")
        return False
    w, h = size
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "size": nearest_api_size(w, h),
        "quality": quality,
        "n": 1,
    }).encode()
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(API_URL, data=body, headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.load(resp)
            b64 = data["data"][0]["b64_json"]
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(b64))
            if is_image(out_path):
                resize_exact(out_path, w, h)
                log(f"API path ok: {out_path} ({model}, {quality})")
                return True
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            log(f"API attempt {attempt + 1} HTTP {e.code}: {detail}")
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            if e.code in (400, 401, 403):
                return False  # non-retryable
        except Exception as e:  # timeout, network, bad payload
            log(f"API attempt {attempt + 1} failed: {e}")
        time.sleep(2)
    return False


def snapshot_codex_outputs():
    root = os.path.expanduser("~/.codex/generated_images")
    return set(glob.glob(os.path.join(root, "*", "ig_*.png")))


def codex_generate(prompt, out_path, size, ref, timeout, retries):
    if not shutil.which("codex"):
        log("codex path unavailable: codex CLI not on PATH")
        return False
    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    os.makedirs(out_dir, exist_ok=True)
    name = os.path.basename(out_path)
    w, h = size
    # Anti-fallback clause is load-bearing: without it codex may "draw" the
    # image with matplotlib/SVG and call it done.
    full_prompt = (
        f"Generate an image: {prompt}\n\n"
        f"Use your image generation tool (do NOT draw it with code, matplotlib, "
        f"or SVG). Save the result as {name} in the current directory."
    )
    cmd = ["codex", "exec", "--skip-git-repo-check", "-C", out_dir,
           "--sandbox", "workspace-write", "--enable", "image_generation"]
    if ref:
        cmd += ["-i", ref]
    cmd.append(full_prompt)
    for attempt in range(retries + 1):
        before = snapshot_codex_outputs()
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            log(f"codex attempt {attempt + 1}: timeout after {timeout}s")
            continue
        if os.path.exists(out_path) and is_image(out_path):
            resize_exact(out_path, w, h)
            log(f"codex path ok: {out_path}")
            return True
        # Salvage: codex generated the file but did not cp it into cwd.
        new = sorted(snapshot_codex_outputs() - before, key=os.path.getmtime)
        if new:
            shutil.copy(new[-1], out_path)
            resize_exact(out_path, w, h)
            log(f"codex path ok (salvaged {os.path.basename(new[-1])})")
            return True
        blob = (r.stdout or "") + (r.stderr or "")
        if "TooManyRequests" in blob or "429" in blob:
            wait = 5 * (attempt + 1)
            log(f"codex attempt {attempt + 1}: rate-limited, backing off {wait}s")
            time.sleep(wait)
            continue
        log(f"codex attempt {attempt + 1}: no image produced (rc={r.returncode}) "
            f"{blob[-200:].strip()}")
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="1024x1024",
                    help="exact WxH pixels, e.g. 1080x1440 (post-resized)")
    ap.add_argument("--model", default="gpt-image-1-mini",
                    help="API model (gpt-image-1-mini | gpt-image-2 | ...)")
    ap.add_argument("--quality", default="low", choices=["low", "medium", "high"],
                    help="API quality tier — scout on low, finalize higher")
    ap.add_argument("--ref", default=None, help="reference image (codex path only)")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--retries", type=int, default=2)
    args = ap.parse_args()

    try:
        w, h = (int(x) for x in args.size.lower().split("x"))
    except ValueError:
        log(f"bad --size {args.size!r}, want WxH")
        return 2
    size = (w, h)
    if args.ref and not os.path.exists(args.ref):
        log(f"--ref not found: {args.ref}")
        return 2

    via_codex = os.environ.get("GEN_IMAGE_VIA_CODEX") == "1"
    if args.ref and not via_codex:
        log("WARN: --ref is only honored on the codex path (API edits deferred)")

    if via_codex:
        if codex_generate(args.prompt, args.out, size, args.ref,
                          args.timeout, args.retries):
            return 0
        log("codex path failed — falling back to API path")
    ok = api_generate(args.prompt, args.out, size, args.model, args.quality,
                      args.timeout, args.retries)
    if ok:
        return 0
    if not os.environ.get("OPENAI_API_KEY") and not via_codex:
        log("nothing to try: set OPENAI_API_KEY (primary) or GEN_IMAGE_VIA_CODEX=1")
        return 2
    log("all paths failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
