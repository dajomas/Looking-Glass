"""Screenshot-based wall assertions; no application rendering changes."""
import io
import json
import math
import time
import uuid
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
    """Poll coherent, visible screenshots, never accepting a zero-width baseline."""
    deadline = time.monotonic() + timeout / 1000
    last, screenshot = {}, None
    while time.monotonic() < deadline:
        try:
            before = page.evaluate(SAMPLE, overlay)
            last = {"before": before}
            if not before.get("ready"):
                # Screenshots provide a browser paint opportunity without a fixed sleep.
                screenshot = page.screenshot(scale="css", timeout=max(1, int((deadline - time.monotonic()) * 1000)))
                continue
            screenshot = page.screenshot(scale="css", timeout=max(1, int((deadline - time.monotonic()) * 1000)))
            after = page.evaluate(SAMPLE, overlay)
            last["after"] = after
            if before != after:
                last["reason"] = "path/geometry/DOM changed across screenshot"
                continue
            with Image.open(io.BytesIO(screenshot)) as source:
                image = source.convert("RGB")
            if list(image.size) != before["viewport"]:
                last["reason"] = "screenshot and CSS viewport dimensions differ"
                continue
            left, right, row = before["strip"]
            count = sum(1 for col in range(left, right + 1)
                        if (lambda c: c[0] > 235 and 65 < c[1] < 130 and c[2] > 180)(image.getpixel((col, row))))
            last["painted_width"] = count
            # Strong-colour pixels can exclude antialiased edge pixels. This
            # absolute credibility check supplements, not replaces, zoom +/-1.
            credible = max(1, math.floor(expected) - 2, minimum) <= count <= math.ceil(expected) + 1
            correct_css = abs(before["screenWidth"] - expected) <= .01
            stable_zoom = reference is None or abs(count - reference) <= 1
            if credible and correct_css and stable_zoom:
                return count
            last["reason"] = "paint/CSS width or zoom invariant not satisfied"
        except Exception as error:
            last["error"] = f"{type(error).__name__}: {error}"
    folder = Path(diagnostic_dir) if diagnostic_dir is not None else Path("test-results/wall-paint")
    stem = folder / ("wall-paint-" + uuid.uuid4().hex)
    last.update(expected=expected, reference=reference, minimum=minimum, timeout_ms=timeout, overlay=overlay)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        if screenshot is None:
            screenshot = page.screenshot(scale="css", timeout=1000)
        stem.with_suffix(".png").write_bytes(screenshot)
        last["screenshot"] = str(stem.with_suffix(".png"))
        stem.with_suffix(".json").write_text(json.dumps(last, indent=2), encoding="utf-8")
    except Exception as error:
        last["diagnostic_error"] = f"{type(error).__name__}: {error}"
    raise AssertionError("Wall paint did not converge: " + json.dumps(last, sort_keys=True))
