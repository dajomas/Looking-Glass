"""Screenshot-based wall assertions; no application rendering changes."""
import copy
import io
import json
import math
import time
import uuid
from collections import deque
from pathlib import Path

from PIL import Image


SAMPLE = r"""selector => {
  let probe = window.__lgWallPaintProbe;
  if (!probe) {
    probe = {ids: new WeakMap(), next: 1, revision: 0};
    probe.observer = new MutationObserver(records => probe.revision += records.length);
    window.__lgWallPaintProbe = probe;
  }
  probe.revision += probe.observer.takeRecords().length;
  const el = document.querySelector(selector + ' .w-wall');
  const result = {document: performance.timeOrigin, revision: probe.revision,
    viewport: [innerWidth, innerHeight], slider: document.querySelector('#wall-width')?.value};
  if (!el?.isConnected) return {...result, ready: false, reason: 'missing/disconnected path'};
  if (!probe.ids.has(el)) probe.ids.set(el, probe.next++);
  probe.observer.observe(el.ownerSVGElement, {attributes: true, childList: true, subtree: true});
  for (let node = el.ownerSVGElement.parentElement; node; node = node.parentElement)
    probe.observer.observe(node, {attributes: true});
  result.node = probe.ids.get(el);
  result.d = el.getAttribute('d');
  const matrix = el.getScreenCTM(), clip = el.closest('.viewport');
  if (!matrix || !clip) return {...result, ready: false, reason: 'missing CTM/viewport'};
  const css = getComputedStyle(el), rect = clip.getBoundingClientRect();
  result.matrix = [matrix.a, matrix.b, matrix.c, matrix.d, matrix.e, matrix.f];
  result.stroke = css.stroke; result.cssWidth = css.strokeWidth;
  result.screenWidth = parseFloat(css.strokeWidth) * Math.hypot(matrix.a, matrix.b);
  result.styles = [];
  let visible = true;
  for (let node = el; node; node = node.parentElement) {
    const style = getComputedStyle(node);
    result.styles.push([style.display, style.visibility, style.opacity]);
    if (style.display === 'none' || style.visibility !== 'visible' || Number(style.opacity) <= 0)
      visible = false;
  }
  const x0 = rect.left + clip.clientLeft, y0 = rect.top + clip.clientTop;
  result.clip = [x0, y0, x0 + clip.clientWidth, y0 + clip.clientHeight];
  const point = new DOMPoint(100, 100).matrixTransform(matrix);
  const left = Math.floor(point.x) - 15, right = left + 30, row = Math.round(point.y);
  result.strip = [left, right, row];
  result.ready = visible && el.isConnected &&
    [...result.matrix, result.screenWidth, point.x, point.y, ...result.clip].every(Number.isFinite) &&
    result.screenWidth > 0 && left >= Math.max(0, result.clip[0]) &&
    right < Math.min(innerWidth, result.clip[2]) && row >= Math.max(0, result.clip[1]) &&
    row < Math.min(innerHeight, result.clip[3]);
  result.reason = result.ready ? 'ready' : 'invisible/nonfinite/clipped sample';
  return result;
}"""


def painted_width(page, overlay, *, expected, reference=None, minimum=1,
                  timeout=5000, diagnostic_dir=None):
    """Preserve completed measurements independently of later capture failures."""
    started = time.monotonic()
    deadline = started + timeout / 1000
    history = deque(maxlen=8)
    last_completed = last_capture = latest_error = None
    attempts = 0
    while time.monotonic() < deadline:
        attempts += 1
        attempt = {"attempt": attempts, "phase": "probe-before"}
        capture = None
        try:
            before = page.evaluate(SAMPLE, overlay)
            attempt["before"] = before
            remaining_ms = int((deadline - time.monotonic()) * 1000)
            if remaining_ms <= 0:
                attempt["reason"] = "budget exhausted before capture"
                break
            attempt.update(phase="screenshot", capture_timeout_ms=remaining_ms)
            capture = page.screenshot(scale="css", timeout=remaining_ms)
            attempt["phase"] = "probe-after"
            after = page.evaluate(SAMPLE, overlay)
            attempt["after"] = after
            if before != after:
                attempt["reason"] = "path/geometry/DOM changed across screenshot"
                continue
            if not before.get("ready"):
                attempt["reason"] = before.get("reason", "sample not ready")
                continue
            attempt["phase"] = "pixels"
            with Image.open(io.BytesIO(capture)) as source:
                image = source.convert("RGB")
            if list(image.size) != before["viewport"]:
                attempt["reason"] = "screenshot and CSS viewport dimensions differ"
                continue
            left, right, row = before["strip"]
            count = sum(1 for col in range(left, right + 1)
                        if (lambda c: c[0] > 235 and 65 < c[1] < 130 and c[2] > 180)(image.getpixel((col, row))))
            credible = max(1, math.floor(expected) - 2, minimum) <= count <= math.ceil(expected) + 1
            correct_css = abs(before["screenWidth"] - expected) <= .01
            stable_zoom = reference is None or abs(count - reference) <= 1
            attempt.update(phase="completed", painted_width=count, credible=credible,
                           correct_css=correct_css, stable_zoom=stable_zoom,
                           reason="accepted" if credible and correct_css and stable_zoom else
                           "paint/CSS width or zoom invariant not satisfied")
            last_completed = {"sample": copy.deepcopy(attempt), "png": capture}
            if credible and correct_css and stable_zoom:
                return count
        except Exception as error:
            attempt["error"] = f"{type(error).__name__}: {error}"
            latest_error = copy.deepcopy(attempt)
        finally:
            attempt["elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
            if capture is not None:
                last_capture = {"sample": copy.deepcopy(attempt), "png": capture}
            history.append(copy.deepcopy(attempt))
    selected = last_completed if last_completed is not None else last_capture
    diagnostic = dict(expected=expected, reference=reference, minimum=minimum,
        timeout_ms=timeout, overlay=overlay, attempts=attempts, history=list(history),
        latest_error=latest_error,
        last_completed=last_completed["sample"] if last_completed else None,
        latest_attempt=history[-1] if history else None,
        saved_sample=selected["sample"] if selected else None,
        capture_source="last_completed" if last_completed else "last_capture" if last_capture else None,
        screenshot=None, diagnostic_errors=[])
    folder = Path(diagnostic_dir) if diagnostic_dir is not None else Path("test-results/wall-paint")
    stem = folder / ("wall-paint-" + uuid.uuid4().hex)
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except Exception as error:
        diagnostic["diagnostic_errors"].append(f"mkdir: {type(error).__name__}: {error}")
    if selected is not None:
        try:
            stem.with_suffix(".png").write_bytes(selected["png"])
            diagnostic["screenshot"] = str(stem.with_suffix(".png"))
        except Exception as error:
            diagnostic["diagnostic_errors"].append(f"PNG: {type(error).__name__}: {error}")
    try:
        stem.with_suffix(".json").write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")
    except Exception as error:
        diagnostic["diagnostic_errors"].append(f"JSON: {type(error).__name__}: {error}")
    raise AssertionError("Wall paint did not converge: " + json.dumps(diagnostic, sort_keys=True))
