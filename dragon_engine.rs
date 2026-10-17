//! Dragon Pixel processing engine (PyO3 extension).
//!
//! Build (development):
//!     maturin develop --release
//! Build (wheel):
//!     maturin build --release
//!
//! Module: `dragon_engine`
//!
//! All functions take an RGBA8888 buffer (`w * h * 4` bytes) and return
//! a freshly-allocated buffer of the same size. The Python editor falls
//! back to pure-Python implementations when this extension is missing.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

/// Engine version — kept in sync with Python `APP_VERSION`.
const VERSION: &str = "0.3.0";

#[inline]
fn to_u8(v: f32) -> u8 {
    if v <= 0.0 {
        0
    } else if v >= 255.0 {
        255
    } else {
        (v + 0.5) as u8
    }
}

fn check(w: usize, h: usize, data: &[u8]) -> PyResult<()> {
    if w == 0 || h == 0 {
        return Err(PyValueError::new_err("empty image"));
    }
    let expected = w
        .checked_mul(h)
        .and_then(|n| n.checked_mul(4))
        .ok_or_else(|| PyValueError::new_err("image dimensions overflow"))?;
    if data.len() != expected {
        return Err(PyValueError::new_err(format!(
            "buffer size mismatch: got {}, expected {} ({}×{}×4)",
            data.len(),
            expected,
            w,
            h
        )));
    }
    Ok(())
}

fn to_f32(data: &[u8]) -> Vec<f32> {
    data.iter().map(|&b| b as f32).collect()
}

fn from_f32(buf: &[f32]) -> Vec<u8> {
    buf.iter().map(|&v| to_u8(v)).collect()
}

// ─────────────── Box blur helpers (O(n) sliding window) ───────────────

fn box_h(src: &[f32], dst: &mut [f32], w: usize, h: usize, r: usize) {
    if r == 0 {
        dst.copy_from_slice(src);
        return;
    }
    let win = (2 * r + 1) as f32;
    for y in 0..h {
        let row = y * w * 4;
        for c in 0..4 {
            let base = row + c;
            let mut sum = src[base] * (r as f32);
            for i in 0..=r {
                sum += src[base + i.min(w - 1) * 4];
            }
            for x in 0..w {
                dst[base + x * 4] = sum / win;
                let out_i = (x as isize - r as isize).clamp(0, w as isize - 1) as usize;
                let in_i = (x as isize + r as isize + 1).clamp(0, w as isize - 1) as usize;
                sum -= src[base + out_i * 4];
                sum += src[base + in_i * 4];
            }
        }
    }
}

fn box_v(src: &[f32], dst: &mut [f32], w: usize, h: usize, r: usize) {
    if r == 0 {
        dst.copy_from_slice(src);
        return;
    }
    let win = (2 * r + 1) as f32;
    let stride = w * 4;
    for x in 0..w {
        for c in 0..4 {
            let base = x * 4 + c;
            let mut sum = src[base] * (r as f32);
            for i in 0..=r {
                sum += src[base + i.min(h - 1) * stride];
            }
            for y in 0..h {
                dst[base + y * stride] = sum / win;
                let out_i = (y as isize - r as isize).clamp(0, h as isize - 1) as usize;
                let in_i = (y as isize + r as isize + 1).clamp(0, h as isize - 1) as usize;
                sum -= src[base + out_i * stride];
                sum += src[base + in_i * stride];
            }
        }
    }
}

fn blur_passes(w: usize, h: usize, data: &[u8], radius: f32, passes: usize) -> Vec<u8> {
    let r = radius.round().max(0.0) as usize;
    if r == 0 {
        return data.to_vec();
    }
    let mut cur = to_f32(data);
    let mut tmp = vec![0.0f32; cur.len()];
    for _ in 0..passes {
        box_h(&cur, &mut tmp, w, h, r);
        box_v(&tmp, &mut cur, w, h, r);
    }
    from_f32(&cur)
}

// ─────────────── Module version ───────────────

#[pyfunction]
fn version() -> &'static str {
    VERSION
}

// ─────────────── Blur ───────────────

#[pyfunction]
fn gaussian_blur<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    radius: f32,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    Ok(PyBytes::new(py, &blur_passes(w, h, data, radius, 3)))
}

#[pyfunction]
fn box_blur<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    radius: f32,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    Ok(PyBytes::new(py, &blur_passes(w, h, data, radius, 1)))
}

// ─────────────── Color & Tone ───────────────

#[pyfunction]
fn sharpen<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    amount: f32,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let src = to_f32(data);
    let mut out = src.clone();
    for y in 0..h {
        for x in 0..w {
            let i = (y * w + x) * 4;
            let up = (y.saturating_sub(1) * w + x) * 4;
            let dn = ((y + 1).min(h - 1) * w + x) * 4;
            let lf = (y * w + x.saturating_sub(1)) * 4;
            let rt = (y * w + (x + 1).min(w - 1)) * 4;
            for c in 0..3 {
                let blur = (src[i + c] + src[up + c] + src[dn + c] + src[lf + c] + src[rt + c]) / 5.0;
                out[i + c] = src[i + c] + (src[i + c] - blur) * amount;
            }
        }
    }
    Ok(PyBytes::new(py, &from_f32(&out)))
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn adjust<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    brightness: f32,
    contrast: f32,
    saturation: f32,
    hue: f32,
    gamma: f32,
    exposure: f32,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = Vec::with_capacity(data.len());
    let cf = (100.0 + contrast) / 100.0;
    let sf = 1.0 + saturation / 100.0;
    for px in data.chunks_exact(4) {
        let mut r = px[0] as f32 / 255.0;
        let mut g = px[1] as f32 / 255.0;
        let mut b = px[2] as f32 / 255.0;
        if exposure != 0.0 {
            let f = 2.0f32.powf(exposure);
            r *= f;
            g *= f;
            b *= f;
        }
        if brightness != 0.0 {
            let bv = brightness / 100.0;
            r += bv;
            g += bv;
            b += bv;
        }
        if contrast != 0.0 {
            r = (r - 0.5) * cf + 0.5;
            g = (g - 0.5) * cf + 0.5;
            b = (b - 0.5) * cf + 0.5;
        }
        if (gamma - 1.0).abs() > 1e-6 && gamma > 0.0 {
            let inv = 1.0 / gamma;
            r = r.clamp(0.0, 1.0).powf(inv);
            g = g.clamp(0.0, 1.0).powf(inv);
            b = b.clamp(0.0, 1.0).powf(inv);
        }
        if hue != 0.0 {
            let mx = r.max(g).max(b);
            let mn = r.min(g).min(b);
            let d = mx - mn;
            let mut hh = if d.abs() < 1e-6 {
                0.0
            } else if (mx - r).abs() < 1e-6 {
                (((g - b) / d) % 6.0 + 6.0) % 6.0
            } else if (mx - g).abs() < 1e-6 {
                (b - r) / d + 2.0
            } else {
                (r - g) / d + 4.0
            };
            hh = (hh / 6.0 + hue / 360.0).rem_euclid(1.0);
            let s = if mx > 0.0 { d / mx } else { 0.0 };
            let v = mx;
            let i = (hh * 6.0).floor();
            let f = hh * 6.0 - i;
            let p = v * (1.0 - s);
            let q = v * (1.0 - f * s);
            let t = v * (1.0 - (1.0 - f) * s);
            let (rr, gg, bb) = match (i as i32) % 6 {
                0 => (v, t, p),
                1 => (q, v, p),
                2 => (p, v, t),
                3 => (p, q, v),
                4 => (t, p, v),
                _ => (v, p, q),
            };
            r = rr;
            g = gg;
            b = bb;
        }
        if saturation != 0.0 {
            let lum = r * 0.299 + g * 0.587 + b * 0.114;
            r = lum + (r - lum) * sf;
            g = lum + (g - lum) * sf;
            b = lum + (b - lum) * sf;
        }
        out.push(to_u8(r * 255.0));
        out.push(to_u8(g * 255.0));
        out.push(to_u8(b * 255.0));
        out.push(px[3]);
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn invert<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8])
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = data.to_vec();
    for px in out.chunks_exact_mut(4) {
        px[0] = 255 - px[0];
        px[1] = 255 - px[1];
        px[2] = 255 - px[2];
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn grayscale<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8])
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = data.to_vec();
    for px in out.chunks_exact_mut(4) {
        let l = (px[0] as f32 * 0.299 + px[1] as f32 * 0.587 + px[2] as f32 * 0.114 + 0.5) as u8;
        px[0] = l;
        px[1] = l;
        px[2] = l;
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn sepia<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8])
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = data.to_vec();
    for px in out.chunks_exact_mut(4) {
        let r = px[0] as f32;
        let g = px[1] as f32;
        let b = px[2] as f32;
        px[0] = to_u8(0.393 * r + 0.769 * g + 0.189 * b);
        px[1] = to_u8(0.349 * r + 0.686 * g + 0.168 * b);
        px[2] = to_u8(0.272 * r + 0.534 * g + 0.131 * b);
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn posterize<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], levels: i32)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let step = 255.0 / (levels.max(2) as f32 - 1.0);
    let mut out = data.to_vec();
    for px in out.chunks_exact_mut(4) {
        for c in 0..3 {
            px[c] = to_u8((px[c] as f32 / step).round() * step);
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn threshold<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], level: i32)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = data.to_vec();
    for px in out.chunks_exact_mut(4) {
        let l = px[0] as f32 * 0.299 + px[1] as f32 * 0.587 + px[2] as f32 * 0.114;
        let v = if l >= level as f32 { 255 } else { 0 };
        px[0] = v;
        px[1] = v;
        px[2] = v;
    }
    Ok(PyBytes::new(py, &out))
}

// ─────────────── Geometry ───────────────

#[pyfunction]
fn resize<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    nw: usize,
    nh: usize,
    bilinear: bool,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    if nw == 0 || nh == 0 {
        return Err(PyValueError::new_err("invalid target size"));
    }
    let mut out = vec![0u8; nw * nh * 4];
    if !bilinear {
        for y in 0..nh {
            let sy = (y * h / nh).min(h - 1);
            for x in 0..nw {
                let sx = (x * w / nw).min(w - 1);
                let si = (sy * w + sx) * 4;
                let di = (y * nw + x) * 4;
                out[di..di + 4].copy_from_slice(&data[si..si + 4]);
            }
        }
        return Ok(PyBytes::new(py, &out));
    }
    for y in 0..nh {
        let fy = ((y as f32 + 0.5) * h as f32 / nh as f32 - 0.5).clamp(0.0, (h - 1) as f32);
        let y0 = fy.floor() as usize;
        let y1 = (y0 + 1).min(h - 1);
        let wy = fy - y0 as f32;
        for x in 0..nw {
            let fx = ((x as f32 + 0.5) * w as f32 / nw as f32 - 0.5).clamp(0.0, (w - 1) as f32);
            let x0 = fx.floor() as usize;
            let x1 = (x0 + 1).min(w - 1);
            let wx = fx - x0 as f32;
            for c in 0..4 {
                let p00 = data[(y0 * w + x0) * 4 + c] as f32;
                let p01 = data[(y0 * w + x1) * 4 + c] as f32;
                let p10 = data[(y1 * w + x0) * 4 + c] as f32;
                let p11 = data[(y1 * w + x1) * 4 + c] as f32;
                let v = p00 * (1.0 - wx) * (1.0 - wy)
                    + p01 * wx * (1.0 - wy)
                    + p10 * (1.0 - wx) * wy
                    + p11 * wx * wy;
                out[(y * nw + x) * 4 + c] = to_u8(v);
            }
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn rotate<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], turns: i32)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let t = ((turns % 4) + 4) % 4;
    let (nw, nh) = if t % 2 == 0 { (w, h) } else { (h, w) };
    let mut out = vec![0u8; nw * nh * 4];
    for y in 0..nh {
        for x in 0..nw {
            let (sx, sy) = match t {
                1 => (y, h - 1 - x),
                2 => (w - 1 - x, h - 1 - y),
                3 => (w - 1 - y, x),
                _ => (x, y),
            };
            let si = (sy * w + sx) * 4;
            let di = (y * nw + x) * 4;
            out[di..di + 4].copy_from_slice(&data[si..si + 4]);
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn flip<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], horizontal: bool)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = vec![0u8; data.len()];
    for y in 0..h {
        for x in 0..w {
            let (sx, sy) = if horizontal {
                (w - 1 - x, y)
            } else {
                (x, h - 1 - y)
            };
            let si = (sy * w + sx) * 4;
            let di = (y * w + x) * 4;
            out[di..di + 4].copy_from_slice(&data[si..si + 4]);
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn crop<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    x: usize,
    y: usize,
    cw: usize,
    ch: usize,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    if cw == 0 || ch == 0 || x + cw > w || y + ch > h {
        return Err(PyValueError::new_err("invalid crop rectangle"));
    }
    let mut out = vec![0u8; cw * ch * 4];
    for row in 0..ch {
        let si = ((y + row) * w + x) * 4;
        let di = row * cw * 4;
        out[di..di + cw * 4].copy_from_slice(&data[si..si + cw * 4]);
    }
    Ok(PyBytes::new(py, &out))
}

// ─────────────── Blur variants ───────────────

#[pyfunction]
fn motion_blur<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    distance: f32,
    angle_deg: f32,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let d = distance.round().max(1.0) as i32;
    let rad = angle_deg.to_radians();
    let dx = rad.cos();
    let dy = rad.sin();
    let mut out = vec![0u8; data.len()];
    for y in 0..h {
        for x in 0..w {
            let mut acc = [0f32; 4];
            let mut cnt = 0.0f32;
            let steps = d.max(1);
            for s in -(steps / 2)..=(steps / 2) {
                let sx = (x as f32 + dx * s as f32).round() as i32;
                let sy = (y as f32 + dy * s as f32).round() as i32;
                let sx = sx.clamp(0, w as i32 - 1) as usize;
                let sy = sy.clamp(0, h as i32 - 1) as usize;
                let i = (sy * w + sx) * 4;
                acc[0] += data[i] as f32;
                acc[1] += data[i + 1] as f32;
                acc[2] += data[i + 2] as f32;
                acc[3] += data[i + 3] as f32;
                cnt += 1.0;
            }
            let oi = (y * w + x) * 4;
            for c in 0..4 {
                out[oi + c] = to_u8(acc[c] / cnt);
            }
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn radial_blur<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    amount: f32,
    quality: i32,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let cx = w as f32 / 2.0;
    let cy = h as f32 / 2.0;
    let steps = quality.max(2);
    let mut out = vec![0u8; data.len()];
    for y in 0..h {
        for x in 0..w {
            let mut acc = [0f32; 4];
            let mut cnt = 0.0f32;
            for s in 0..steps {
                let t = 1.0 + amount * (s as f32 / steps as f32);
                let sx = (cx + (x as f32 - cx) * t).round() as i32;
                let sy = (cy + (y as f32 - cy) * t).round() as i32;
                let sx = sx.clamp(0, w as i32 - 1) as usize;
                let sy = sy.clamp(0, h as i32 - 1) as usize;
                let i = (sy * w + sx) * 4;
                acc[0] += data[i] as f32;
                acc[1] += data[i + 1] as f32;
                acc[2] += data[i + 2] as f32;
                acc[3] += data[i + 3] as f32;
                cnt += 1.0;
            }
            let oi = (y * w + x) * 4;
            for c in 0..4 {
                out[oi + c] = to_u8(acc[c] / cnt);
            }
        }
    }
    Ok(PyBytes::new(py, &out))
}

// ─────────────── Advanced adjustments ───────────────

#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn levels<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    in_black: f32,
    in_white: f32,
    gamma: f32,
    out_black: f32,
    out_white: f32,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut lut = [0u8; 256];
    let denom = (in_white - in_black).max(1.0);
    for v in 0..256 {
        let mut t = ((v as f32) - in_black) / denom;
        t = t.clamp(0.0, 1.0);
        if gamma != 1.0 && gamma > 0.0 {
            t = t.powf(1.0 / gamma);
        }
        lut[v] = to_u8(out_black + t * (out_white - out_black));
    }
    let mut out = data.to_vec();
    for px in out.chunks_exact_mut(4) {
        px[0] = lut[px[0] as usize];
        px[1] = lut[px[1] as usize];
        px[2] = lut[px[2] as usize];
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn color_balance<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    r_shift: f32,
    g_shift: f32,
    b_shift: f32,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = data.to_vec();
    for px in out.chunks_exact_mut(4) {
        px[0] = to_u8(px[0] as f32 + r_shift);
        px[1] = to_u8(px[1] as f32 + g_shift);
        px[2] = to_u8(px[2] as f32 + b_shift);
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn photo_filter<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    r: f32,
    g: f32,
    b: f32,
    density: f32,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = data.to_vec();
    let d = density.clamp(0.0, 1.0);
    for px in out.chunks_exact_mut(4) {
        let fr = px[0] as f32 / 255.0;
        let fg = px[1] as f32 / 255.0;
        let fb = px[2] as f32 / 255.0;
        px[0] = to_u8((fr * (1.0 - d) + (fr * r) * d) * 255.0);
        px[1] = to_u8((fg * (1.0 - d) + (fg * g) * d) * 255.0);
        px[2] = to_u8((fb * (1.0 - d) + (fb * b) * d) * 255.0);
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn high_pass<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], radius: f32)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let blurred = blur_passes(w, h, data, radius, 2);
    let mut out = data.to_vec();
    for i in (0..data.len()).step_by(4) {
        out[i] = to_u8(128.0 + (data[i] as f32 - blurred[i] as f32));
        out[i + 1] = to_u8(128.0 + (data[i + 1] as f32 - blurred[i + 1] as f32));
        out[i + 2] = to_u8(128.0 + (data[i + 2] as f32 - blurred[i + 2] as f32));
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn emboss<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8])
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = data.to_vec();
    for y in 0..h {
        for x in 0..w {
            let i = (y * w + x) * 4;
            let ur = (y.saturating_sub(1) * w + x) * 4;
            let dl = (y * w + x.saturating_sub(1)) * 4;
            for c in 0..3 {
                let v = 128.0 + (data[i + c] as f32 - data[ur + c] as f32)
                    + (data[i + c] as f32 - data[dl + c] as f32);
                out[i + c] = to_u8(v);
            }
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn find_edges<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8])
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut out = data.to_vec();
    for y in 0..h {
        for x in 0..w {
            let i = (y * w + x) * 4;
            let xm = (y * w + x.saturating_sub(1)) * 4;
            let xp = (y * w + (x + 1).min(w - 1)) * 4;
            let ym = (y.saturating_sub(1) * w + x) * 4;
            let yp = ((y + 1).min(h - 1) * w + x) * 4;
            for c in 0..3 {
                let gx = data[xp + c] as f32 - data[xm + c] as f32;
                let gy = data[yp + c] as f32 - data[ym + c] as f32;
                out[i + c] = to_u8((gx * gx + gy * gy).sqrt());
            }
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn pixelate<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], block: usize)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let b = block.max(1);
    let mut out = data.to_vec();
    let mut y = 0;
    while y < h {
        let mut x = 0;
        while x < w {
            let mut acc = [0u32; 4];
            let mut cnt = 0u32;
            for by in 0..b {
                for bx in 0..b {
                    let px = x + bx;
                    let py = y + by;
                    if px < w && py < h {
                        let i = (py * w + px) * 4;
                        for c in 0..4 {
                            acc[c] += data[i + c] as u32;
                        }
                        cnt += 1;
                    }
                }
            }
            if cnt > 0 {
                for by in 0..b {
                    for bx in 0..b {
                        let px = x + bx;
                        let py = y + by;
                        if px < w && py < h {
                            let i = (py * w + px) * 4;
                            for c in 0..4 {
                                out[i + c] = (acc[c] / cnt) as u8;
                            }
                        }
                    }
                }
            }
            x += b;
        }
        y += b;
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn add_noise<'py>(
    py: Python<'py>,
    w: usize,
    h: usize,
    data: &[u8],
    amount: f32,
    seed: u64,
) -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let mut state = seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut rand = || -> f32 {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        ((state & 0xFFFF_FFFF) as f32 / u32::MAX as f32) * 2.0 - 1.0
    };
    let mut out = data.to_vec();
    for px in out.chunks_exact_mut(4) {
        for c in 0..3 {
            px[c] = to_u8(px[c] as f32 + rand() * amount);
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn vignette<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], strength: f32)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let cx = w as f32 / 2.0;
    let cy = h as f32 / 2.0;
    let mut out = data.to_vec();
    for y in 0..h {
        let dy = (y as f32 - cy) / cy;
        for x in 0..w {
            let dx = (x as f32 - cx) / cx;
            let d = (dx * dx + dy * dy).sqrt();
            let k = (1.0 - strength * (d - 0.35).max(0.0)).clamp(0.0, 1.0);
            let i = (y * w + x) * 4;
            out[i] = to_u8(out[i] as f32 * k);
            out[i + 1] = to_u8(out[i + 1] as f32 * k);
            out[i + 2] = to_u8(out[i + 2] as f32 * k);
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn median_filter<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], radius: usize)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let r = radius.max(1) as i32;
    let mut out = data.to_vec();
    let mut window: Vec<u8> = Vec::with_capacity(((2 * r + 1) * (2 * r + 1)) as usize);
    for y in 0..h {
        for x in 0..w {
            let i = (y * w + x) * 4;
            for c in 0..3 {
                window.clear();
                for dy in -r..=r {
                    for dx in -r..=r {
                        let nx = (x as i32 + dx).clamp(0, w as i32 - 1) as usize;
                        let ny = (y as i32 + dy).clamp(0, h as i32 - 1) as usize;
                        window.push(data[(ny * w + nx) * 4 + c]);
                    }
                }
                window.sort_unstable();
                out[i + c] = window[window.len() / 2];
            }
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn dilate<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], radius: usize)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let r = radius.max(1) as i32;
    let mut out = data.to_vec();
    for y in 0..h {
        for x in 0..w {
            let di = (y * w + x) * 4;
            let mut best = [0u8; 4];
            for dy in -r..=r {
                let ny = (y as i32 + dy).clamp(0, h as i32 - 1) as usize;
                for dx in -r..=r {
                    let nx = (x as i32 + dx).clamp(0, w as i32 - 1) as usize;
                    let si = (ny * w + nx) * 4;
                    for c in 0..4 {
                        if data[si + c] > best[c] {
                            best[c] = data[si + c];
                        }
                    }
                }
            }
            out[di..di + 4].copy_from_slice(&best);
        }
    }
    Ok(PyBytes::new(py, &out))
}

#[pyfunction]
fn erode<'py>(py: Python<'py>, w: usize, h: usize, data: &[u8], radius: usize)
    -> PyResult<Bound<'py, PyBytes>> {
    check(w, h, data)?;
    let r = radius.max(1) as i32;
    let mut out = data.to_vec();
    for y in 0..h {
        for x in 0..w {
            let di = (y * w + x) * 4;
            let mut best = [255u8; 4];
            for dy in -r..=r {
                let ny = (y as i32 + dy).clamp(0, h as i32 - 1) as usize;
                for dx in -r..=r {
                    let nx = (x as i32 + dx).clamp(0, w as i32 - 1) as usize;
                    let si = (ny * w + nx) * 4;
                    for c in 0..4 {
                        if data[si + c] < best[c] {
                            best[c] = data[si + c];
                        }
                    }
                }
            }
            out[di..di + 4].copy_from_slice(&best);
        }
    }
    Ok(PyBytes::new(py, &out))
}

// ─────────────── Module registration ───────────────

#[pymodule]
fn dragon_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", VERSION)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(gaussian_blur, m)?)?;
    m.add_function(wrap_pyfunction!(box_blur, m)?)?;
    m.add_function(wrap_pyfunction!(sharpen, m)?)?;
    m.add_function(wrap_pyfunction!(adjust, m)?)?;
    m.add_function(wrap_pyfunction!(invert, m)?)?;
    m.add_function(wrap_pyfunction!(grayscale, m)?)?;
    m.add_function(wrap_pyfunction!(sepia, m)?)?;
    m.add_function(wrap_pyfunction!(posterize, m)?)?;
    m.add_function(wrap_pyfunction!(threshold, m)?)?;
    m.add_function(wrap_pyfunction!(resize, m)?)?;
    m.add_function(wrap_pyfunction!(rotate, m)?)?;
    m.add_function(wrap_pyfunction!(flip, m)?)?;
    m.add_function(wrap_pyfunction!(crop, m)?)?;
    m.add_function(wrap_pyfunction!(motion_blur, m)?)?;
    m.add_function(wrap_pyfunction!(radial_blur, m)?)?;
    m.add_function(wrap_pyfunction!(levels, m)?)?;
    m.add_function(wrap_pyfunction!(color_balance, m)?)?;
    m.add_function(wrap_pyfunction!(photo_filter, m)?)?;
    m.add_function(wrap_pyfunction!(high_pass, m)?)?;
    m.add_function(wrap_pyfunction!(emboss, m)?)?;
    m.add_function(wrap_pyfunction!(find_edges, m)?)?;
    m.add_function(wrap_pyfunction!(pixelate, m)?)?;
    m.add_function(wrap_pyfunction!(add_noise, m)?)?;
    m.add_function(wrap_pyfunction!(vignette, m)?)?;
    m.add_function(wrap_pyfunction!(median_filter, m)?)?;
    m.add_function(wrap_pyfunction!(dilate, m)?)?;
    m.add_function(wrap_pyfunction!(erode, m)?)?;
    Ok(())
}