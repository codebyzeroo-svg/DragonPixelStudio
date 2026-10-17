#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragon Pixel — Professional Creative Studio
============================================
PySide6 + optional Rust engine (dragon_engine, PyO3)

    py -3.12 -m pip install PySide6
    maturin develop --release          # يبني dragon_engine إن أردت
    py -3.12 dragon_pixel.py
"""
from __future__ import annotations

import io
import json
import math
import os
import random
import sys
import time
import traceback
import zipfile
from typing import Any, Callable, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
#   فحص PySide6 قبل أي استيراد — يمنع ModuleNotFoundError المفاجئ
# ═══════════════════════════════════════════════════════════════════
def _ensure_pyside6() -> bool:
    try:
        import PySide6  # noqa: F401
        return True
    except ImportError:
        pass

    bar = "=" * 68
    print("\n" + bar)
    print("⚠  PySide6 غير مثبّت — المحرر الكامل يحتاجه.")
    print(bar)
    print(f"\nPython الحالي: {sys.version.split()[0]}  ({sys.executable})")

    if sys.version_info >= (3, 13):
        print("\n❗ PySide6 لا يدعم Python 3.13+ حالياً (بما فيها 3.14).")
        print("\n   ▸ الحل الأسرع الآن — بدون أي تثبيت:")
        print("        python dragon_lite.py")
        print("\n   ▸ أو استخدم Python 3.12 بالتوازي مع نسختك الحالية:")
        print("        1) نزّل Python 3.12 من https://www.python.org/downloads/")
        print("        2) ثم:")
        print("             py -3.12 -m pip install PySide6")
        print("             py -3.12 dragon_pixel.py")
    else:
        print("\n   ▸ لتثبيت PySide6:")
        print("        python -m pip install PySide6")
        print("\n   ▸ أو استخدم النسخة الخفيفة بدون تثبيت:")
        print("        python dragon_lite.py")

    print("\n" + bar + "\n")
    return False


if not _ensure_pyside6():
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
#   استيرادات PySide6 (بعد التأكد من توفرها)
# ═══════════════════════════════════════════════════════════════════
from PySide6.QtCore import (  # noqa: E402
    Qt, QPoint, QPointF, QRect, QRectF, QSize, QTimer, Signal, QObject,
    QSettings, QStandardPaths, QBuffer, QIODevice, QByteArray,
)
from PySide6.QtGui import (  # noqa: E402
    QImage, QPainter, QColor, QPen, QBrush, QPixmap, QFont, QFontDatabase,
    QIcon, QAction, QKeySequence, QLinearGradient, QRadialGradient,
    QPolygonF, QTransform, QRegion, QBitmap, QPainterPath, QCursor,
)
from PySide6.QtWidgets import (  # noqa: E402
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QToolBar, QDockWidget, QListWidget, QListWidgetItem, QPushButton,
    QSlider, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit,
    QPlainTextEdit, QAbstractSpinBox, QFileDialog, QMessageBox, QInputDialog,
    QColorDialog, QDialog, QDialogButtonBox, QFormLayout, QTabWidget,
    QStatusBar, QGridLayout, QCheckBox, QToolButton, QFontComboBox,
    QProgressBar, QGroupBox,
)

try:
    import dragon_engine as _ENGINE  # type: ignore
    ENGINE_OK = True
    ENGINE_VERSION = _ENGINE.version()
except Exception:
    _ENGINE = None
    ENGINE_OK = False
    ENGINE_VERSION = "none"


APP_NAME = "Dragon Pixel"
APP_VERSION = "0.3.1"
ORG = "DragonPixel"
DPX_EXT = (".dpx", ".dragonpixel")

__version__ = APP_VERSION
__all__ = ["main", "Document", "Layer", "CanvasView", "MainWindow",
           "LayerStyle", "History", "Command"]


def _use_engine() -> bool:
    if not ENGINE_OK:
        return False
    return not QSettings(ORG, ORG).value("force_python", False, type=bool)


# ───────────────────────────── الترجمات ─────────────────────────────
STR: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "Dragon Pixel — Professional Creative Studio",
        "file": "File", "edit": "Edit", "image": "Image", "layer": "Layer",
        "select": "Select", "filter": "Filter", "colors": "Colors",
        "view": "View", "window": "Window", "help": "Help",
        "new": "New…", "open": "Open…", "save": "Save", "save_as": "Save As…",
        "export": "Export…", "export_layers": "Export Layers…",
        "recent": "Recent Files", "quit": "Exit",
        "undo": "Undo", "redo": "Redo", "prefs": "Settings…",
        "resize_image": "Image Size…", "resize_canvas": "Canvas Size…",
        "rot_cw": "Rotate 90° CW", "rot_ccw": "Rotate 90° CCW",
        "rot_180": "Rotate 180°", "flip_h": "Flip Horizontal",
        "flip_v": "Flip Vertical", "crop_sel": "Crop to Selection",
        "new_layer": "New Layer", "dup_layer": "Duplicate Layer",
        "del_layer": "Delete Layer", "merge_down": "Merge Down",
        "flatten": "Flatten Image", "add_mask": "Add Layer Mask",
        "del_mask": "Delete Layer Mask", "inv_mask": "Invert Mask",
        "apply_mask": "Apply Mask", "layer_style": "Layer Style…",
        "sel_all": "All", "deselect": "Deselect", "inv_sel": "Inverse",
        "feather": "Feather…", "expand": "Expand…", "contract": "Contract…",
        "remove_bg": "Remove Background (color-based)",
        "zoom_in": "Zoom In", "zoom_out": "Zoom Out", "fit": "Fit on Screen",
        "actual": "Actual Pixels", "rulers": "Rulers", "grid": "Grid",
        "fullscreen": "Full Screen", "split": "Before / After (split)",
        "brightness_contrast": "Brightness / Contrast…",
        "hue_sat": "Hue / Saturation…", "auto_contrast": "Auto Contrast",
        "invert_colors": "Invert", "grayscale": "Grayscale", "sepia": "Sepia",
        "gaussian_blur": "Gaussian Blur…", "box_blur": "Box Blur…",
        "sharpen": "Sharpen…", "emboss": "Emboss", "find_edges": "Find Edges",
        "pixelate": "Pixelate…", "noise": "Add Noise…", "vignette": "Vignette…",
        "posterize": "Posterize…", "threshold": "Threshold…",
        "motion_blur": "Motion Blur…", "radial_blur": "Radial Blur…",
        "levels": "Levels…", "color_balance": "Color Balance…",
        "photo_filter": "Photo Filter…", "high_pass": "High Pass…",
        "median": "Median…", "dilate": "Dilate", "erode": "Erode",
        "layers": "Layers", "adjustments": "Adjustments", "history": "History",
        "color": "Color", "brushes": "Brushes", "navigator": "Navigator",
        "about": "About Dragon Pixel", "dark": "Dark Theme",
        "light": "Light Theme", "language": "Language",
        "opacity": "Opacity", "blend": "Blend", "fg": "Foreground",
        "bg": "Background", "size": "Size", "hardness": "Hardness",
        "flow": "Flow", "spacing": "Spacing", "tolerance": "Tolerance",
        "symmetry": "Symmetry", "engine": "Engine", "ready": "Ready",
        "restart_lang": "Changing the language requires restarting the application.",
        "weak_device": "Optimize for weak devices",
        "force_python": "Force Python engine (disable Rust)",
        "engine_status": "Engine status",
        "copy": "Copy", "paste": "Paste", "cut": "Cut",
        "paste_as_layer": "Paste as New Layer",
        "reset_view": "Reset View", "templates": "New Project…",
    },
    "ar": {
        "app_title": "دراغون بيكسل — استوديو إبداعي احترافي",
        "file": "ملف", "edit": "تحرير", "image": "صورة", "layer": "طبقة",
        "select": "تحديد", "filter": "فلتر", "colors": "ألوان",
        "view": "عرض", "window": "نافذة", "help": "مساعدة",
        "new": "جديد…", "open": "فتح…", "save": "حفظ", "save_as": "حفظ باسم…",
        "export": "تصدير…", "export_layers": "تصدير الطبقات…",
        "recent": "الملفات الأخيرة", "quit": "خروج",
        "undo": "تراجع", "redo": "إعادة", "prefs": "الإعدادات…",
        "resize_image": "أبعاد الصورة…", "resize_canvas": "أبعاد اللوحة…",
        "rot_cw": "تدوير 90° يمينًا", "rot_ccw": "تدوير 90° يسارًا",
        "rot_180": "تدوير 180°", "flip_h": "قلب أفقي", "flip_v": "قلب رأسي",
        "crop_sel": "قص إلى التحديد",
        "new_layer": "طبقة جديدة", "dup_layer": "نسخ الطبقة",
        "del_layer": "حذف الطبقة", "merge_down": "دمج لأسفل",
        "flatten": "تسوية الصورة", "add_mask": "إضافة قناع",
        "del_mask": "حذف القناع", "inv_mask": "عكس القناع",
        "apply_mask": "تطبيق القناع", "layer_style": "نمط الطبقة…",
        "sel_all": "الكل", "deselect": "إلغاء التحديد", "inv_sel": "عكس",
        "feather": "تنعيم الحواف…", "expand": "توسيع…", "contract": "تقليص…",
        "remove_bg": "إزالة الخلفية (حسب اللون)",
        "zoom_in": "تكبير", "zoom_out": "تصغير", "fit": "ملاءمة الشاشة",
        "actual": "الحجم الفعلي", "rulers": "المساطر", "grid": "الشبكة",
        "fullscreen": "ملء الشاشة", "split": "قبل / بعد",
        "brightness_contrast": "السطوع / التباين…",
        "hue_sat": "تدرج اللون / التشبع…", "auto_contrast": "تباين تلقائي",
        "invert_colors": "عكس الألوان", "grayscale": "تدرج رمادي", "sepia": "سيبيا",
        "gaussian_blur": "تمويه غاوسي…", "box_blur": "تمويه صندوقي…",
        "sharpen": "زيادة الحدة…", "emboss": "نقش بارز", "find_edges": "استخراج الحواف",
        "pixelate": "بكسلة…", "noise": "إضافة تشويش…", "vignette": "تظليل الأطراف…",
        "posterize": "تقليل الألوان…", "threshold": "عتبة…",
        "motion_blur": "تمويه حركي…", "radial_blur": "تمويه شعاعي…",
        "levels": "المستويات…", "color_balance": "توازن الألوان…",
        "photo_filter": "فلتر فوتوغرافي…", "high_pass": "تمرير عالي…",
        "median": "وسيط…", "dilate": "توسيع الشكل", "erode": "تقليص الشكل",
        "layers": "الطبقات", "adjustments": "التعديلات", "history": "السجل",
        "color": "اللون", "brushes": "الفرش", "navigator": "الملاح",
        "about": "حول Dragon Pixel", "dark": "الوضع الداكن", "light": "الوضع الفاتح",
        "language": "اللغة", "opacity": "الشفافية", "blend": "المزج",
        "fg": "الأمامي", "bg": "الخلفي", "size": "الحجم", "hardness": "الصلابة",
        "flow": "التدفق", "spacing": "التباعد", "tolerance": "التسامح",
        "symmetry": "التناظر", "engine": "المحرك", "ready": "جاهز",
        "restart_lang": "تغيير اللغة يتطلب إعادة التشغيل.",
        "weak_device": "تحسين للأجهزة الضعيفة",
        "force_python": "إجبار محرك Python (تعطيل Rust)",
        "engine_status": "حالة المحرك",
        "copy": "نسخ", "paste": "لصق", "cut": "قص",
        "paste_as_layer": "لصق كطبقة جديدة",
        "reset_view": "إعادة ضبط العرض",
        "templates": "مشروع جديد…",
    },
}


def T(key: str) -> str:
    lang = QSettings(ORG, ORG).value("lang", "ar")
    return STR.get(lang, STR["en"]).get(key, STR["en"].get(key, key))


# ──────────────────── أدوات QImage ────────────────────
def qimg_rgba_bytes(img: QImage) -> Tuple[bytearray, int, int]:
    rgba = img.convertToFormat(QImage.Format_RGBA8888)
    w, h = rgba.width(), rgba.height()
    return bytearray(rgba.constBits()), w, h


def bytes_to_qimg(data: bytes, w: int, h: int) -> QImage:
    return QImage(bytes(data), w, h, w * 4, QImage.Format_RGBA8888).copy()


def clamp(v: float, lo: float = 0.0, hi: float = 255.0) -> int:
    return int(lo if v < lo else hi if v > hi else v)


# ──────────────────── دوال المحرك (Rust + Python fallback) ────────────────────
def eng_blur(img, r):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.gaussian_blur(w, h, bytes(d), float(r)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_blur(img, r)


def eng_box_blur(img, r):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.box_blur(w, h, bytes(d), float(r)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_blur(img, r)


def eng_adjust(img, brightness=0.0, contrast=0.0, saturation=0.0,
               hue=0.0, gamma=1.0, exposure=0.0):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.adjust(
                w, h, bytes(d),
                float(brightness), float(contrast), float(saturation),
                float(hue), float(gamma), float(exposure)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_adjust(img, brightness, contrast, saturation, hue, gamma, exposure)


def eng_invert(img):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.invert(w, h, bytes(d)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_invert(img)


def eng_grayscale(img):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.grayscale(w, h, bytes(d)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_grayscale(img)


def eng_sepia(img):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.sepia(w, h, bytes(d)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_sepia(img)


def eng_posterize(img, levels):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.posterize(w, h, bytes(d), int(levels)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_posterize(img, levels)


def eng_threshold(img, level):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.threshold(w, h, bytes(d), int(level)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_threshold(img, level)


def eng_sharpen(img, amount=1.0):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.sharpen(w, h, bytes(d), float(amount)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_sharpen(img, amount)


def eng_motion_blur(img, distance, angle):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.motion_blur(
                w, h, bytes(d), float(distance), float(angle)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_motion_blur(img, distance, angle)


def eng_radial_blur(img, amount, quality=8):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.radial_blur(
                w, h, bytes(d), float(amount), int(quality)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_radial_blur(img, amount, quality)


def eng_levels(img, in_b, in_w, gamma, out_b, out_w):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.levels(
                w, h, bytes(d),
                float(in_b), float(in_w), float(gamma),
                float(out_b), float(out_w)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_levels(img, in_b, in_w, gamma, out_b, out_w)


def eng_color_balance(img, r_s, g_s, b_s):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.color_balance(
                w, h, bytes(d), float(r_s), float(g_s), float(b_s)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_color_balance(img, r_s, g_s, b_s)


def eng_photo_filter(img, r, g, b, density):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.photo_filter(
                w, h, bytes(d), float(r), float(g), float(b),
                float(density)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_photo_filter(img, r, g, b, density)


def eng_high_pass(img, radius):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.high_pass(
                w, h, bytes(d), float(radius)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_high_pass(img, radius)


def eng_emboss(img):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.emboss(w, h, bytes(d)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_emboss(img)


def eng_find_edges(img):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.find_edges(w, h, bytes(d)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_edges(img)


def eng_pixelate(img, block):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.pixelate(w, h, bytes(d), int(block)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_pixelate(img, block)


def eng_add_noise(img, amount):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            seed = random.getrandbits(64)
            return bytes_to_qimg(_ENGINE.add_noise(
                w, h, bytes(d), float(amount), seed), w, h)
        except Exception:
            traceback.print_exc()
    return _py_noise(img, amount)


def eng_vignette(img, strength):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.vignette(
                w, h, bytes(d), float(strength)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_vignette(img, strength)


def eng_median(img, radius):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.median_filter(
                w, h, bytes(d), int(radius)), w, h)
        except Exception:
            traceback.print_exc()
    return _py_median(img, radius)


def eng_dilate(img, radius):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.dilate(w, h, bytes(d), int(radius)), w, h)
        except Exception:
            traceback.print_exc()
    data, w, h = qimg_rgba_bytes(img)
    r = max(1, int(radius))
    out = bytearray(data)
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            for c in range(4):
                m = 0
                for dy in range(-r, r + 1):
                    yy = max(0, min(h - 1, y + dy))
                    for dx in range(-r, r + 1):
                        xx = max(0, min(w - 1, x + dx))
                        v = data[(yy * w + xx) * 4 + c]
                        if v > m:
                            m = v
                out[i + c] = m
    return bytes_to_qimg(out, w, h)


def eng_erode(img, radius):
    if _use_engine():
        try:
            d, w, h = qimg_rgba_bytes(img)
            return bytes_to_qimg(_ENGINE.erode(w, h, bytes(d), int(radius)), w, h)
        except Exception:
            traceback.print_exc()
    data, w, h = qimg_rgba_bytes(img)
    r = max(1, int(radius))
    out = bytearray(data)
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            for c in range(4):
                m = 255
                for dy in range(-r, r + 1):
                    yy = max(0, min(h - 1, y + dy))
                    for dx in range(-r, r + 1):
                        xx = max(0, min(w - 1, x + dx))
                        v = data[(yy * w + xx) * 4 + c]
                        if v < m:
                            m = v
                out[i + c] = m
    return bytes_to_qimg(out, w, h)


# ──────────────────── Fallbacks Python ────────────────────
def _py_blur(img, radius):
    if radius <= 0:
        return img.copy()
    w, h = img.width(), img.height()
    f = max(2, int(radius))
    sw = max(1, w // f)
    sh = max(1, h // f)
    small = img.scaled(sw, sh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    return small.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)


def _py_adjust(img, brightness=0.0, contrast=0.0, saturation=0.0,
               hue=0.0, gamma=1.0, exposure=0.0):
    data, w, h = qimg_rgba_bytes(img)
    cf = (100.0 + contrast) / 100.0
    sf = 1.0 + saturation / 100.0
    exp_f = 2.0 ** exposure if exposure else 1.0
    need_hue = abs(hue) > 0.01
    for i in range(0, len(data), 4):
        r = data[i] / 255.0
        g = data[i + 1] / 255.0
        b = data[i + 2] / 255.0
        if exposure:
            r *= exp_f; g *= exp_f; b *= exp_f
        if brightness:
            bv = brightness / 100.0
            r += bv; g += bv; b += bv
        if contrast:
            r = (r - 0.5) * cf + 0.5
            g = (g - 0.5) * cf + 0.5
            b = (b - 0.5) * cf + 0.5
        if gamma != 1.0 and gamma > 0:
            inv = 1.0 / gamma
            r = (max(0.0, r)) ** inv
            g = (max(0.0, g)) ** inv
            b = (max(0.0, b)) ** inv
        if need_hue:
            mx = max(r, g, b); mn = min(r, g, b); d = mx - mn
            if d > 1e-9:
                if abs(mx - r) < 1e-9:
                    hh = (((g - b) / d) % 6.0) / 6.0
                elif abs(mx - g) < 1e-9:
                    hh = ((b - r) / d + 2.0) / 6.0
                else:
                    hh = ((r - g) / d + 4.0) / 6.0
                hh = (hh + hue / 360.0) % 1.0
                i6 = int(hh * 6); f = hh * 6 - i6
                p = mx * (1 - d / mx) if mx > 0 else 0
                q = mx * (1 - f * d / mx) if mx > 0 else 0
                t = mx * (1 - (1 - f) * d / mx) if mx > 0 else 0
                r, g, b = [(mx, t, p), (q, mx, p), (p, mx, t),
                           (p, q, mx), (t, p, mx), (mx, p, q)][i6 % 6]
        if saturation:
            lum = r * 0.299 + g * 0.587 + b * 0.114
            r = lum + (r - lum) * sf
            g = lum + (g - lum) * sf
            b = lum + (b - lum) * sf
        data[i] = clamp(r * 255)
        data[i + 1] = clamp(g * 255)
        data[i + 2] = clamp(b * 255)
    return bytes_to_qimg(data, w, h)


def _py_invert(img):
    data, w, h = qimg_rgba_bytes(img)
    for i in range(0, len(data), 4):
        data[i] = 255 - data[i]
        data[i + 1] = 255 - data[i + 1]
        data[i + 2] = 255 - data[i + 2]
    return bytes_to_qimg(data, w, h)


def _py_grayscale(img):
    data, w, h = qimg_rgba_bytes(img)
    for i in range(0, len(data), 4):
        v = clamp(data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114)
        data[i] = data[i + 1] = data[i + 2] = v
    return bytes_to_qimg(data, w, h)


def _py_sepia(img):
    data, w, h = qimg_rgba_bytes(img)
    for i in range(0, len(data), 4):
        r, g, b = data[i], data[i + 1], data[i + 2]
        data[i] = clamp(0.393 * r + 0.769 * g + 0.189 * b)
        data[i + 1] = clamp(0.349 * r + 0.686 * g + 0.168 * b)
        data[i + 2] = clamp(0.272 * r + 0.534 * g + 0.131 * b)
    return bytes_to_qimg(data, w, h)


def _py_posterize(img, levels):
    data, w, h = qimg_rgba_bytes(img)
    step = 255.0 / max(1, levels - 1)
    for i in range(0, len(data), 4):
        for c in range(3):
            data[i + c] = clamp(round(data[i + c] / step) * step)
    return bytes_to_qimg(data, w, h)


def _py_threshold(img, level):
    data, w, h = qimg_rgba_bytes(img)
    for i in range(0, len(data), 4):
        lum = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114
        v = 255 if lum >= level else 0
        data[i] = data[i + 1] = data[i + 2] = v
    return bytes_to_qimg(data, w, h)


def _py_sharpen(img, amount=1.0):
    w, h = img.width(), img.height()
    blurred = _py_blur(img, 2)
    data_s = bytearray(img.convertToFormat(QImage.Format_RGBA8888).constBits())
    data_b = bytes(blurred.convertToFormat(QImage.Format_RGBA8888).constBits())
    for i in range(0, len(data_s), 4):
        for c in range(3):
            v = data_s[i + c] + (data_s[i + c] - data_b[i + c]) * amount
            data_s[i + c] = clamp(v)
    return bytes_to_qimg(data_s, w, h)


def _py_noise(img, amount):
    data, w, h = qimg_rgba_bytes(img)
    rng = random.Random()
    n = amount * 1.5
    for i in range(0, len(data), 4):
        for c in range(3):
            data[i + c] = clamp(data[i + c] + rng.uniform(-n, n))
    return bytes_to_qimg(data, w, h)


def _py_vignette(img, strength):
    data, w, h = qimg_rgba_bytes(img)
    cx, cy = w / 2.0, h / 2.0
    for y in range(h):
        dy = (y - cy) / cy if cy else 0
        for x in range(w):
            dx = (x - cx) / cx if cx else 0
            d = math.sqrt(dx * dx + dy * dy)
            k = max(0.0, min(1.0, 1.0 - strength * max(0.0, d - 0.35)))
            i = (y * w + x) * 4
            data[i] = clamp(data[i] * k)
            data[i + 1] = clamp(data[i + 1] * k)
            data[i + 2] = clamp(data[i + 2] * k)
    return bytes_to_qimg(data, w, h)


def _py_emboss(img):
    src, w, h = qimg_rgba_bytes(img)
    out = bytearray(len(src))
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            ur = ((max(0, y - 1)) * w + x) * 4
            dl = (y * w + max(0, x - 1)) * 4
            for c in range(3):
                v = 128 + (src[i + c] - src[ur + c]) + (src[i + c] - src[dl + c])
                out[i + c] = clamp(v)
            out[i + 3] = src[i + 3]
    return bytes_to_qimg(out, w, h)


def _py_edges(img):
    src, w, h = qimg_rgba_bytes(img)
    out = bytearray(len(src))
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            xm = (y * w + max(0, x - 1)) * 4
            xp = (y * w + min(w - 1, x + 1)) * 4
            ym = (max(0, y - 1) * w + x) * 4
            yp = (min(h - 1, y + 1) * w + x) * 4
            for c in range(3):
                gx = src[xp + c] - src[xm + c]
                gy = src[yp + c] - src[ym + c]
                out[i + c] = clamp(math.sqrt(gx * gx + gy * gy))
            out[i + 3] = src[i + 3]
    return bytes_to_qimg(out, w, h)


def _py_pixelate(img, block):
    w, h = img.width(), img.height()
    block = max(1, block)
    sw, sh = max(1, w // block), max(1, h // block)
    small = img.scaled(sw, sh, Qt.IgnoreAspectRatio, Qt.FastTransformation)
    return small.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)


def _py_motion_blur(img, distance, angle):
    d = max(1, int(round(distance)))
    rad = math.radians(angle)
    dx, dy = math.cos(rad), math.sin(rad)
    src, w, h = qimg_rgba_bytes(img)
    out = bytearray(len(src))
    steps = 2 * d + 1
    for y in range(h):
        for x in range(w):
            acc = [0, 0, 0, 0]
            for s in range(-d, d + 1):
                sx = max(0, min(w - 1, int(round(x + dx * s))))
                sy = max(0, min(h - 1, int(round(y + dy * s))))
                i = (sy * w + sx) * 4
                for c in range(4):
                    acc[c] += src[i + c]
            oi = (y * w + x) * 4
            for c in range(4):
                out[oi + c] = acc[c] // steps
    return bytes_to_qimg(out, w, h)


def _py_radial_blur(img, amount, quality=8):
    src, w, h = qimg_rgba_bytes(img)
    out = bytearray(len(src))
    cx, cy = w / 2.0, h / 2.0
    steps = max(2, int(quality))
    for y in range(h):
        for x in range(w):
            acc = [0, 0, 0, 0]
            for s in range(steps):
                t = 1.0 + amount * (s / steps)
                sx = max(0, min(w - 1, int(round(cx + (x - cx) * t))))
                sy = max(0, min(h - 1, int(round(cy + (y - cy) * t))))
                i = (sy * w + sx) * 4
                for c in range(4):
                    acc[c] += src[i + c]
            oi = (y * w + x) * 4
            for c in range(4):
                out[oi + c] = acc[c] // steps
    return bytes_to_qimg(out, w, h)


def _py_levels(img, in_b, in_w, gamma, out_b, out_w):
    data, w, h = qimg_rgba_bytes(img)
    denom = max(1.0, float(in_w) - float(in_b))
    lut = [0] * 256
    for v in range(256):
        t = max(0.0, min(1.0, (v - in_b) / denom))
        if gamma != 1.0 and gamma > 0:
            t = t ** (1.0 / gamma)
        lut[v] = clamp(out_b + t * (out_w - out_b))
    for i in range(0, len(data), 4):
        data[i] = lut[data[i]]
        data[i + 1] = lut[data[i + 1]]
        data[i + 2] = lut[data[i + 2]]
    return bytes_to_qimg(data, w, h)


def _py_color_balance(img, r_s, g_s, b_s):
    data, w, h = qimg_rgba_bytes(img)
    for i in range(0, len(data), 4):
        data[i] = clamp(data[i] + r_s)
        data[i + 1] = clamp(data[i + 1] + g_s)
        data[i + 2] = clamp(data[i + 2] + b_s)
    return bytes_to_qimg(data, w, h)


def _py_photo_filter(img, r, g, b, density):
    data, w, h = qimg_rgba_bytes(img)
    d = max(0.0, min(1.0, float(density)))
    for i in range(0, len(data), 4):
        fr = data[i] / 255.0
        fg = data[i + 1] / 255.0
        fb = data[i + 2] / 255.0
        data[i] = clamp((fr * (1.0 - d) + fr * r * d) * 255.0)
        data[i + 1] = clamp((fg * (1.0 - d) + fg * g * d) * 255.0)
        data[i + 2] = clamp((fb * (1.0 - d) + fb * b * d) * 255.0)
    return bytes_to_qimg(data, w, h)


def _py_high_pass(img, radius):
    w, h = img.width(), img.height()
    f = max(2, int(round(max(1.0, radius) * 2)))
    sw = max(1, w // f)
    sh = max(1, h // f)
    small = img.scaled(sw, sh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    blurred = small.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    src, _, _ = qimg_rgba_bytes(img)
    blr = bytes(blurred.convertToFormat(QImage.Format_RGBA8888).constBits())
    out = bytearray(src)
    for i in range(0, len(src), 4):
        for c in range(3):
            out[i + c] = clamp(128.0 + (src[i + c] - blr[i + c]))
    return bytes_to_qimg(out, w, h)


def _py_median(img, radius):
    src, w, h = qimg_rgba_bytes(img)
    out = bytearray(src)
    r = max(1, int(radius))
    win: List[int] = []
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            for c in range(3):
                win.clear()
                for dy in range(-r, r + 1):
                    yy = max(0, min(h - 1, y + dy))
                    for dx in range(-r, r + 1):
                        xx = max(0, min(w - 1, x + dx))
                        win.append(src[(yy * w + xx) * 4 + c])
                win.sort()
                out[i + c] = win[len(win) // 2]
    return bytes_to_qimg(out, w, h)


def _dilate_mask_py(img: QImage, radius: int) -> QImage:
    if radius <= 0:
        return img.copy()
    gray = img.convertToFormat(QImage.Format_Grayscale8)
    w, h = gray.width(), gray.height()
    stride = gray.bytesPerLine()
    src_bytes = bytes(gray.constBits())
    r = max(1, int(radius))
    tmp = bytearray(w * h)
    for y in range(h):
        row = y * stride
        for x in range(w):
            m = 0
            lo = max(0, x - r); hi = min(w - 1, x + r)
            for xx in range(lo, hi + 1):
                v = src_bytes[row + xx]
                if v > m:
                    m = v
            tmp[y * w + x] = m
    out = bytearray(src_bytes)
    for y in range(h):
        for x in range(w):
            m = 0
            lo = max(0, y - r); hi = min(h - 1, y + r)
            for yy in range(lo, hi + 1):
                v = tmp[yy * w + x]
                if v > m:
                    m = v
            out[y * stride + x] = m
    return QImage(bytes(out), w, h, stride, QImage.Format_Grayscale8).copy()


QT_BLEND = {
    "Normal": QPainter.CompositionMode_SourceOver,
    "Multiply": QPainter.CompositionMode_Multiply,
    "Screen": QPainter.CompositionMode_Screen,
    "Overlay": QPainter.CompositionMode_Overlay,
    "Soft Light": QPainter.CompositionMode_SoftLight,
    "Hard Light": QPainter.CompositionMode_HardLight,
    "Darken": QPainter.CompositionMode_Darken,
    "Lighten": QPainter.CompositionMode_Lighten,
    "Difference": QPainter.CompositionMode_Difference,
    "Add": QPainter.CompositionMode_Plus,
    "Subtract": QPainter.CompositionMode_Difference,
}
BLEND_MODES = list(QT_BLEND.keys())


def flood_fill_mask(img: QImage, x0: int, y0: int, tolerance: int) -> QImage:
    src, w, h = qimg_rgba_bytes(img)
    if not (0 <= x0 < w and 0 <= y0 < h):
        m = QImage(w, h, QImage.Format_Grayscale8); m.fill(0); return m
    i0 = (y0 * w + x0) * 4
    sr, sg, sb = src[i0], src[i0 + 1], src[i0 + 2]
    tol = tolerance * 3
    mask = bytearray(w * h)
    stack = [(x0, y0)]
    while stack:
        x, y = stack.pop()
        idx = y * w + x
        if mask[idx]:
            continue
        i = idx * 4
        if abs(src[i] - sr) + abs(src[i + 1] - sg) + abs(src[i + 2] - sb) > tol:
            continue
        mask[idx] = 255
        if x > 0: stack.append((x - 1, y))
        if x < w - 1: stack.append((x + 1, y))
        if y > 0: stack.append((x, y - 1))
        if y < h - 1: stack.append((x, y + 1))
    return QImage(bytes(mask), w, h, w, QImage.Format_Grayscale8).copy()


# ──────────────────── LayerStyle ────────────────────
class LayerStyle:
    def __init__(self):
        self.stroke_enabled = False
        self.stroke_color = "#000000"
        self.stroke_width = 2
        self.shadow_enabled = False
        self.shadow_color = "#00000099"
        self.shadow_dx = 2
        self.shadow_dy = 2
        self.shadow_blur = 4
        self.glow_enabled = False
        self.glow_color = "#FFD166"
        self.glow_radius = 6

    def render(self, src: QImage) -> QImage:
        out = QImage(src.width(), src.height(), QImage.Format_ARGB32_Premultiplied)
        out.fill(Qt.transparent)
        p = QPainter(out)
        p.setRenderHint(QPainter.Antialiasing, True)

        if self.shadow_enabled:
            sh = QImage(src.width(), src.height(), QImage.Format_ARGB32_Premultiplied)
            sh.fill(Qt.transparent)
            ps = QPainter(sh)
            ps.drawImage(0, 0, src)
            ps.setCompositionMode(QPainter.CompositionMode_SourceIn)
            ps.fillRect(0, 0, sh.width(), sh.height(), QColor(self.shadow_color))
            ps.end()
            if self.shadow_blur > 0:
                sh = eng_blur(sh, self.shadow_blur)
            p.drawImage(self.shadow_dx, self.shadow_dy, sh)

        if self.glow_enabled:
            gl = QImage(src.width(), src.height(), QImage.Format_ARGB32_Premultiplied)
            gl.fill(Qt.transparent)
            pg = QPainter(gl)
            pg.drawImage(0, 0, src)
            pg.setCompositionMode(QPainter.CompositionMode_SourceIn)
            pg.fillRect(0, 0, gl.width(), gl.height(), QColor(self.glow_color))
            pg.end()
            if self.glow_radius > 0:
                gl = eng_blur(gl, self.glow_radius)
            p.drawImage(0, 0, gl)

        if self.stroke_enabled and self.stroke_width > 0:
            alpha = src.convertToFormat(QImage.Format_Alpha8)
            expanded = _dilate_mask_py(alpha, self.stroke_width)
            stroke_img = QImage(src.width(), src.height(), QImage.Format_ARGB32_Premultiplied)
            stroke_img.fill(QColor(self.stroke_color))
            psm = QPainter(stroke_img)
            psm.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            psm.drawImage(0, 0, expanded)
            psm.end()
            p.drawImage(0, 0, stroke_img)

        p.drawImage(0, 0, src)
        p.end()
        return out


# ──────────────────── Layer ────────────────────
class Layer:
    def __init__(self, name, w, h, image=None, kind="pixel", params=None):
        self.name = name
        self.visible = True
        self.opacity = 1.0
        self.blend = "Normal"
        self.locked = False
        self.kind = kind
        self.params = params or {}
        self.mask = None
        self.mask_enabled = True
        self.style = None
        if image is None:
            image = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
            image.fill(Qt.transparent)
        self.image = image.convertToFormat(QImage.Format_ARGB32_Premultiplied)

    def clone(self, new_name=None):
        L = Layer(new_name or self.name + " copy",
                  self.image.width(), self.image.height(),
                  self.image.copy(), self.kind, dict(self.params))
        L.visible = self.visible
        L.opacity = self.opacity
        L.blend = self.blend
        L.locked = self.locked
        L.mask = None if self.mask is None else self.mask.copy()
        L.mask_enabled = self.mask_enabled
        L.style = self.style
        return L

    def effective_image(self):
        img = self.image
        if self.style is not None and (self.style.stroke_enabled or
                                       self.style.shadow_enabled or
                                       self.style.glow_enabled):
            img = self.style.render(img)
        if self.mask is None or not self.mask_enabled:
            return img
        out = img.copy()
        p = QPainter(out)
        p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        p.drawImage(0, 0, self.mask.convertToFormat(QImage.Format_Alpha8))
        p.end()
        return out

    def nbytes(self):
        n = self.image.width() * self.image.height() * 4
        if self.mask is not None:
            n += self.mask.width() * self.mask.height()
        return n


# ──────────────────── History ────────────────────
class Command:
    def __init__(self, label, undo, redo, size=0):
        self.label = label
        self._undo = undo
        self._redo = redo
        self.size = size

    def undo(self):
        self._undo()

    def redo(self):
        self._redo()


class History:
    def __init__(self, limit=60, max_bytes=1024 * 1024 * 1024):
        self.entries: List[Command] = []
        self.index = -1
        self.limit = limit
        self.max_bytes = max_bytes
        self.on_change = None

    def _notify(self):
        if self.on_change:
            self.on_change()

    def push(self, cmd):
        del self.entries[self.index + 1:]
        self.entries.append(cmd)
        self.index = len(self.entries) - 1
        while len(self.entries) > self.limit:
            self.entries.pop(0)
            self.index -= 1
        while sum(c.size for c in self.entries) > self.max_bytes and len(self.entries) > 1:
            self.entries.pop(0)
            self.index -= 1
        self.index = max(0, self.index)
        self._notify()

    def can_undo(self):
        return self.index >= 0

    def can_redo(self):
        return self.index + 1 < len(self.entries)

    def undo(self):
        if self.can_undo():
            self.entries[self.index].undo()
            self.index -= 1
            self._notify()

    def redo(self):
        if self.can_redo():
            self.index += 1
            self.entries[self.index].redo()
            self._notify()

    def jump_to(self, pos):
        while self.index > pos:
            self.entries[self.index].undo()
            self.index -= 1
        while self.index < pos:
            self.index += 1
            self.entries[self.index].redo()
        self._notify()


# ──────────────────── Document ────────────────────
class Document(QObject):
    changed = Signal()
    structure_changed = Signal()

    def __init__(self, width, height, name="Untitled"):
        super().__init__()
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.name = name
        self.path = None
        self.layers: List[Layer] = []
        self.active = 0
        self.selection = None
        weak = QSettings(ORG, ORG).value("weak_device", False, type=bool)
        self.history = History(limit=15 if weak else 60,
                               max_bytes=(128 if weak else 1024) * 1024 * 1024)
        self.history.on_change = self._on_history
        self._cache = None
        self._dirty = True
        self.baseline = None
        self._comp_cache = {}

    def _on_history(self):
        self.invalidate()
        self.changed.emit()

    def invalidate(self):
        self._dirty = True
        self._cache = None
        self._comp_cache.clear()

    def active_layer(self):
        if 0 <= self.active < len(self.layers):
            return self.layers[self.active]
        return None

    def add_layer(self, layer, index=None):
        if layer.image.width() != self.width or layer.image.height() != self.height:
            layer.image = layer.image.scaled(self.width, self.height,
                                             Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        if index is None:
            index = len(self.layers)
        self.layers.insert(index, layer)
        self.active = index
        self.invalidate()
        self.structure_changed.emit()
        return index

    def new_layer(self, name=None):
        return self.add_layer(Layer(name or f"Layer {len(self.layers) + 1}",
                                    self.width, self.height))

    def remove_layer(self, index):
        if 0 <= index < len(self.layers):
            del self.layers[index]
            self.active = min(index, len(self.layers) - 1) if self.layers else 0
            self.invalidate()
            self.structure_changed.emit()

    def composite(self):
        if self._cache is not None and not self._dirty:
            return self._cache
        out = QImage(self.width, self.height, QImage.Format_ARGB32_Premultiplied)
        out.fill(Qt.transparent)
        p = QPainter(out)
        for layer in self.layers:
            if not layer.visible:
                continue
            p.setOpacity(layer.opacity)
            p.setCompositionMode(QT_BLEND.get(layer.blend, QPainter.CompositionMode_SourceOver))
            p.drawImage(0, 0, layer.effective_image())
        p.end()
        self._cache = out
        self._dirty = False
        return out

    def commit_pixels(self, label, layer_index, before):
        layer = self.layers[layer_index]
        after = layer.image.copy()
        doc = self

        def undo():
            doc.layers[layer_index].image = before.copy()
            doc.invalidate()
            doc.changed.emit()

        def redo():
            doc.layers[layer_index].image = after.copy()
            doc.invalidate()
            doc.changed.emit()

        w = before.width(); h = before.height()
        self.history.push(Command(label, undo, redo, w * h * 8))

    def push_custom(self, label, undo_fn, redo_fn, size=0):
        self.history.push(Command(label, undo_fn, redo_fn, size))

    # ─── helpers for transformations ───
    def _snapshot_layers(self):
        return [(l.image.copy(), None if l.mask is None else l.mask.copy(),
                 l.visible, l.opacity, l.blend) for l in self.layers]

    def _restore_layers(self, snap):
        for l, (im, m, vis, op, bl) in zip(self.layers, snap):
            l.image = im.copy()
            l.mask = None if m is None else m.copy()
            l.visible, l.opacity, l.blend = vis, op, bl

    def _commit_transform(self, label, before_size, before_snap, run):
        run()
        after_size = (self.width, self.height)
        after_snap = self._snapshot_layers()
        self.invalidate()
        self.structure_changed.emit()

        def undo():
            self._restore_layers(before_snap)
            self.width, self.height = before_size
            self.invalidate()
            self.structure_changed.emit()

        def redo():
            self._restore_layers(after_snap)
            self.width, self.height = after_size
            self.invalidate()
            self.structure_changed.emit()

        # ✅ FIX: width() و height() دوال — كانت بدون أقواس سابقاً
        mem = sum(im.width() * im.height() * 4 for im, *_ in before_snap)
        self.push_custom(label, undo, redo, mem)

    def rotate(self, turns):
        turns = int(turns) % 4
        if turns == 0:
            return
        bs, bsnap = (self.width, self.height), self._snapshot_layers()

        def run():
            for l in self.layers:
                l.image = l.image.transformed(QTransform().rotate(turns * 90))
                if l.mask is not None:
                    l.mask = l.mask.transformed(QTransform().rotate(turns * 90))
            if self.selection is not None:
                self.selection = self.selection.transformed(QTransform().rotate(turns * 90))
            self.width = self.layers[0].image.width()
            self.height = self.layers[0].image.height()

        self._commit_transform("Rotate", bs, bsnap, run)

    def flip(self, horizontal):
        before = [l.image.copy() for l in self.layers]
        for l in self.layers:
            l.image = l.image.mirrored(horizontal, not horizontal)
            if l.mask is not None:
                l.mask = l.mask.mirrored(horizontal, not horizontal)
        if self.selection is not None:
            self.selection = self.selection.mirrored(horizontal, not horizontal)
        self.invalidate()
        self.changed.emit()
        after = [l.image.copy() for l in self.layers]

        def undo():
            for l, im in zip(self.layers, before):
                l.image = im.copy()
            self.invalidate()
            self.changed.emit()

        def redo():
            for l, im in zip(self.layers, after):
                l.image = im.copy()
            self.invalidate()
            self.changed.emit()

        self.push_custom("Flip", undo, redo,
                         sum(im.width() * im.height() * 4 for im in before))

    def resize_image(self, nw, nh):
        nw, nh = max(1, nw), max(1, nh)
        bs, bsnap = (self.width, self.height), self._snapshot_layers()

        def run():
            for l in self.layers:
                l.image = l.image.scaled(nw, nh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                if l.mask is not None:
                    l.mask = l.mask.scaled(nw, nh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.width, self.height = nw, nh
            self.selection = None

        self._commit_transform("Image Size", bs, bsnap, run)

    def resize_canvas(self, nw, nh):
        nw, nh = max(1, nw), max(1, nh)
        bs, bsnap = (self.width, self.height), self._snapshot_layers()

        def run():
            for l in self.layers:
                new = QImage(nw, nh, QImage.Format_ARGB32_Premultiplied)
                new.fill(Qt.transparent)
                p = QPainter(new)
                p.drawImage(0, 0, l.image)
                p.end()
                l.image = new
                if l.mask is not None:
                    nm = QImage(nw, nh, QImage.Format_Grayscale8)
                    nm.fill(0)
                    p = QPainter(nm)
                    p.drawImage(0, 0, l.mask)
                    p.end()
                    l.mask = nm
            self.width, self.height = nw, nh
            self.selection = None

        self._commit_transform("Canvas Size", bs, bsnap, run)

    def crop(self, x, y, w, h):
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        w = max(1, min(w, self.width - x))
        h = max(1, min(h, self.height - y))
        bs, bsnap = (self.width, self.height), self._snapshot_layers()

        def run():
            for l in self.layers:
                l.image = l.image.copy(x, y, w, h)
                if l.mask is not None:
                    l.mask = l.mask.copy(x, y, w, h)
            self.width, self.height = w, h
            self.selection = None

        self._commit_transform("Crop", bs, bsnap, run)

    def merge_down(self):
        i = self.active
        if i <= 0 or i >= len(self.layers):
            return
        top = self.layers[i]
        bottom = self.layers[i - 1]
        b_state = (bottom.image.copy(),
                   None if bottom.mask is None else bottom.mask.copy(),
                   bottom.opacity, bottom.blend)
        t_state = (top.name, top.image.copy())

        result = QImage(self.width, self.height, QImage.Format_ARGB32_Premultiplied)
        result.fill(Qt.transparent)
        p = QPainter(result)
        p.setOpacity(bottom.opacity)
        p.setCompositionMode(QT_BLEND.get(bottom.blend, QPainter.CompositionMode_SourceOver))
        p.drawImage(0, 0, bottom.effective_image())
        p.setOpacity(top.opacity)
        p.setCompositionMode(QT_BLEND.get(top.blend, QPainter.CompositionMode_SourceOver))
        p.drawImage(0, 0, top.effective_image())
        p.end()

        bottom.image = result
        bottom.mask = None
        bottom.opacity = 1.0
        bottom.blend = "Normal"
        del self.layers[i]
        self.active = i - 1
        self.invalidate()
        self.structure_changed.emit()

        def undo():
            b_im, b_mask, b_op, b_bl = b_state
            self.layers[i - 1].image = b_im.copy()
            self.layers[i - 1].mask = None if b_mask is None else b_mask.copy()
            self.layers[i - 1].opacity = b_op
            self.layers[i - 1].blend = b_bl
            t_name, t_im = t_state
            self.layers.insert(i, Layer(t_name, self.width, self.height, t_im.copy()))
            self.active = i
            self.invalidate()
            self.structure_changed.emit()

        self.push_custom("Merge Down", undo, lambda: None,
                         (b_state[0].width() * b_state[0].height()
                          + t_state[1].width() * t_state[1].height()) * 4)

    def flatten(self):
        comp = self.composite().copy()
        bs, bsnap = (self.width, self.height), self._snapshot_layers()

        def run():
            self.layers = [Layer("Background", self.width, self.height, comp)]
            self.active = 0

        self._commit_transform("Flatten", bs, bsnap, run)

    def snapshot_baseline(self):
        self.baseline = self.composite().copy()


# ──────────────────── AppState ────────────────────
class AppState:
    def __init__(self):
        self.tool = "move"
        self.fg = QColor("#FF4D4D")
        self.bg = QColor("#171A22")
        self.brush_size = 24
        self.brush_hardness = 70
        self.brush_opacity = 100
        self.brush_flow = 100
        self.brush_spacing = 20
        self.tolerance = 24
        self.symmetry = False
        self.feather = 0
        self.show_rulers = True
        self.show_grid = False
        self.split_view = False
        self.clone_source = None
        self.clone_offset = None
        self.dodge_mode = "Midtones"


TOOLS = [
    ("move", "Move", "تحريك", "V", True, "✥"),
    ("marquee_rect", "Rectangular Marquee", "تحديد مستطيل", "M", True, "▭"),
    ("marquee_ellipse", "Elliptical Marquee", "تحديد بيضاوي", "", True, "◯"),
    ("lasso", "Lasso", "لاسو", "L", True, "⌒"),
    ("magic_wand", "Magic Wand", "العصا السحرية", "W", True, "✦"),
    ("crop", "Crop", "قص", "C", True, "⌗"),
    ("brush", "Brush", "فرشاة", "B", True, "✎"),
    ("pencil", "Pencil", "قلم", "N", True, "✐"),
    ("eraser", "Eraser", "ممحاة", "E", True, "⌫"),
    ("blur_tool", "Blur", "تمويه", "", True, "◍"),
    ("sharpen_tool", "Sharpen", "حدة", "", True, "◈"),
    ("dodge", "Dodge", "تفتيح", "O", True, "☀"),
    ("burn", "Burn", "تغميق", "", True, "☾"),
    ("clone", "Clone Stamp", "ختم النسخ", "S", True, "⊘"),
    ("heal", "Healing Brush", "فرشاة المعالجة", "J", True, "✚"),
    ("smudge", "Smudge", "تلطيخ", "", True, "≈"),
    ("color_replace", "Color Replace", "استبدال اللون", "", True, "◎"),
    ("gradient", "Gradient", "تدرج", "G", True, "▤"),
    ("bucket", "Paint Bucket", "سطل الطلاء", "K", True, "▨"),
    ("eyedropper", "Eyedropper", "قطارة", "I", True, "⌖"),
    ("text", "Text", "نص", "T", True, "T"),
    ("shape", "Shape", "شكل", "U", True, "◧"),
    ("line", "Line", "خط", "", True, "／"),
    ("hand", "Hand", "يد", "H", True, "✋"),
    ("zoom", "Zoom", "تكبير", "Z", True, "🔍"),
    ("selection", "Selection Tool", "أداة التحديد", "A", False, "⬚"),
    ("poly_lasso", "Polygonal Lasso", "لاسو متعدد", "", False, "⬡"),
    ("quick_sel", "Quick Selection", "تحديد سريع", "", False, "◌"),
    ("persp_crop", "Perspective Crop", "قص منظوري", "", False, "⧉"),
]


# ──────────────────── الحوارات ────────────────────
class NewDocDialog(QDialog):
    PRESETS = [
        ("Custom", 1280, 720),
        ("Full HD 1920×1080", 1920, 1080),
        ("YouTube Thumbnail 1280×720", 1280, 720),
        ("Instagram Post 1080×1080", 1080, 1080),
        ("Instagram Story 1080×1920", 1080, 1920),
        ("A4 300dpi 2480×3508", 2480, 3508),
        ("Gaming Wallpaper 2560×1440", 2560, 1440),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("new"))
        lay = QFormLayout(self)
        self.preset = QComboBox()
        for name, _, _ in self.PRESETS:
            self.preset.addItem(name)
        self.w = QSpinBox(); self.w.setRange(1, 20000); self.w.setValue(1280)
        self.h = QSpinBox(); self.h.setRange(1, 20000); self.h.setValue(720)
        self.background = QComboBox()
        self.background.addItems(["Transparent", "White", "Black", "Background color"])
        lay.addRow("Preset", self.preset)
        lay.addRow("Width", self.w)
        lay.addRow("Height", self.h)
        lay.addRow("Background", self.background)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)
        self.preset.currentIndexChanged.connect(self._apply_preset)

    def _apply_preset(self, i):
        _, w, h = self.PRESETS[i]
        self.w.setValue(w)
        self.h.setValue(h)


class ParamDialog(QDialog):
    def __init__(self, parent, title, specs, apply_fn, on_preview, on_accept):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.apply_fn = apply_fn
        self.on_preview = on_preview
        self.on_accept = on_accept
        weak = QSettings(ORG, ORG).value("weak_device", False, type=bool)
        interval = 250 if weak else 100
        self._timer = QTimer(self, singleShot=True, interval=interval)
        self._timer.timeout.connect(self._update_preview)
        self._result = None
        lay = QFormLayout(self)
        self.widgets = {}
        for key, label, lo, hi, default, is_float in specs:
            if is_float:
                w = QDoubleSpinBox(); w.setRange(lo, hi)
                w.setSingleStep(0.1); w.setValue(default)
            else:
                w = QSpinBox(); w.setRange(int(lo), int(hi)); w.setValue(int(default))
            w.valueChanged.connect(lambda *_: self._timer.start())
            self.widgets[key] = w
            lay.addRow(label, w)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)
        self.resize(340, 140)

    def values(self):
        return {k: w.value() for k, w in self.widgets.items()}

    def _update_preview(self):
        try:
            self._result = self.apply_fn(self.values())
            self.on_preview(self._result)
        except Exception as exc:
            print("preview error:", exc)
            self.on_preview(None)

    def accept(self):
        self._timer.stop()
        self._update_preview()
        self.on_preview(None)
        if self._result is not None:
            self.on_accept(self._result)
        super().accept()

    def reject(self):
        self._timer.stop()
        self.on_preview(None)
        super().reject()


class TextDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Text")
        lay = QFormLayout(self)
        self.text = QTextEdit()
        self.text.setPlainText("Dragon Pixel")
        self.text.setFixedHeight(90)
        self.family = QFontComboBox()
        self.family.setCurrentFont(QFont("Arial"))
        self.size = QSpinBox(); self.size.setRange(6, 800); self.size.setValue(64)
        self.color = QPushButton("Color…")
        self._color = QColor("#F3F4F6")
        self.color.setStyleSheet(f"background:{self._color.name()}")
        self.color.clicked.connect(self._pick_color)
        self.bold = QCheckBox("Bold")
        self.italic = QCheckBox("Italic")
        self.align = QComboBox(); self.align.addItems(["Left", "Center", "Right"])
        lay.addRow("Text", self.text)
        lay.addRow("Font", self.family)
        lay.addRow("Size", self.size)
        lay.addRow("Color", self.color)
        lay.addRow(self.bold, self.italic)
        lay.addRow("Align", self.align)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def _pick_color(self):
        c = QColorDialog.getColor(self._color, self, "Text Color")
        if c.isValid():
            self._color = c
            self.color.setStyleSheet(f"background:{c.name()}")

    def result_params(self, x, y):
        return {"text": self.text.toPlainText(),
                "family": self.family.currentFont().family(),
                "size": self.size.value(), "color": self._color.name(),
                "bold": self.bold.isChecked(), "italic": self.italic.isChecked(),
                "align": self.align.currentText(), "x": x, "y": y}


def render_text_layer(params, w, h):
    img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    f = QFont(params.get("family", "Arial"), int(params.get("size", 64)))
    f.setBold(bool(params.get("bold", False)))
    f.setItalic(bool(params.get("italic", False)))
    p.setFont(f)
    p.setPen(QColor(params.get("color", "#F3F4F6")))
    flags = {"Left": Qt.AlignLeft, "Center": Qt.AlignHCenter,
             "Right": Qt.AlignRight}.get(params.get("align", "Left"), Qt.AlignLeft)
    rect = QRectF(params.get("x", 0), params.get("y", 0),
                  w - params.get("x", 0), h)
    p.drawText(rect, flags | Qt.AlignTop | Qt.TextWordWrap, params.get("text", ""))
    p.end()
    return img


class LayerStyleDialog(QDialog):
    def __init__(self, parent, style):
        super().__init__(parent)
        self.setWindowTitle(T("layer_style"))
        lay = QFormLayout(self)
        s = style or LayerStyle()

        self.stroke_cb = QCheckBox("Stroke")
        self.stroke_cb.setChecked(s.stroke_enabled)
        self.stroke_color = QPushButton(s.stroke_color)
        self.stroke_color.setStyleSheet(f"background:{s.stroke_color}")
        self.stroke_color.clicked.connect(lambda: self._pick(self.stroke_color))
        self.stroke_width = QSpinBox()
        self.stroke_width.setRange(1, 50)
        self.stroke_width.setValue(s.stroke_width)
        g1 = QGroupBox("Stroke"); gl1 = QFormLayout(g1)
        gl1.addRow(self.stroke_cb)
        gl1.addRow("Color", self.stroke_color)
        gl1.addRow("Width", self.stroke_width)
        lay.addRow(g1)

        self.shadow_cb = QCheckBox("Drop Shadow")
        self.shadow_cb.setChecked(s.shadow_enabled)
        self.shadow_color = QPushButton(s.shadow_color)
        self.shadow_color.setStyleSheet(f"background:{s.shadow_color}")
        self.shadow_color.clicked.connect(lambda: self._pick(self.shadow_color))
        self.shadow_dx = QSpinBox(); self.shadow_dx.setRange(-100, 100); self.shadow_dx.setValue(s.shadow_dx)
        self.shadow_dy = QSpinBox(); self.shadow_dy.setRange(-100, 100); self.shadow_dy.setValue(s.shadow_dy)
        self.shadow_blur = QSpinBox(); self.shadow_blur.setRange(0, 100); self.shadow_blur.setValue(s.shadow_blur)
        g2 = QGroupBox("Shadow"); gl2 = QFormLayout(g2)
        gl2.addRow(self.shadow_cb)
        gl2.addRow("Color", self.shadow_color)
        gl2.addRow("dx", self.shadow_dx)
        gl2.addRow("dy", self.shadow_dy)
        gl2.addRow("blur", self.shadow_blur)
        lay.addRow(g2)

        self.glow_cb = QCheckBox("Outer Glow")
        self.glow_cb.setChecked(s.glow_enabled)
        self.glow_color = QPushButton(s.glow_color)
        self.glow_color.setStyleSheet(f"background:{s.glow_color}")
        self.glow_color.clicked.connect(lambda: self._pick(self.glow_color))
        self.glow_radius = QSpinBox(); self.glow_radius.setRange(0, 100); self.glow_radius.setValue(s.glow_radius)
        g3 = QGroupBox("Glow"); gl3 = QFormLayout(g3)
        gl3.addRow(self.glow_cb)
        gl3.addRow("Color", self.glow_color)
        gl3.addRow("radius", self.glow_radius)
        lay.addRow(g3)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def _pick(self, btn):
        c = QColorDialog.getColor(QColor(btn.text() if btn.text().startswith("#") else "#000000"),
                                  self, "Color", QColorDialog.ShowAlphaChannel)
        if c.isValid():
            btn.setText(c.name(QColor.HexArgb))
            btn.setStyleSheet(f"background:{c.name()}")

    def result_style(self):
        s = LayerStyle()
        s.stroke_enabled = self.stroke_cb.isChecked()
        s.stroke_color = self.stroke_color.text()
        s.stroke_width = self.stroke_width.value()
        s.shadow_enabled = self.shadow_cb.isChecked()
        s.shadow_color = self.shadow_color.text()
        s.shadow_dx = self.shadow_dx.value()
        s.shadow_dy = self.shadow_dy.value()
        s.shadow_blur = self.shadow_blur.value()
        s.glow_enabled = self.glow_cb.isChecked()
        s.glow_color = self.glow_color.text()
        s.glow_radius = self.glow_radius.value()
        return s


# ──────────────────── CanvasView ────────────────────
class CanvasView(QWidget):
    cursor_moved = Signal(int, int)
    zoom_changed = Signal(float)
    status = Signal(str)

    def __init__(self, doc, state, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.state = state
        self.zoom = 1.0
        self.offset = QPointF(20, 20)
        self.preview = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(200, 200)
        self.weak = QSettings(ORG, ORG).value("weak_device", False, type=bool)

        self._drawing = False
        self._last_img_pos = None
        self._stroke_before = None
        self._panning = False
        self._pan_start = QPointF()
        self._sel_start = None
        self._lasso_points = []
        self._crop_rect = None
        self._shape_start = None
        self._rubber_rect = None
        self._clone_anchor = None
        self._smudge_buf = None
        self._smudge_pick = None

        doc.changed.connect(self.update)
        doc.structure_changed.connect(self._on_struct)
        self._checker = self._make_checker()

    def _make_checker(self):
        pm = QPixmap(16, 16)
        pm.fill(QColor("#2b2f3a"))
        p = QPainter(pm)
        p.fillRect(0, 0, 8, 8, QColor("#3a3f4d"))
        p.fillRect(8, 8, 8, 8, QColor("#3a3f4d"))
        p.end()
        return pm

    def _on_struct(self):
        self.fit_to_screen()
        self.update()

    def image_rect(self):
        return QRectF(self.offset.x(), self.offset.y(),
                      self.doc.width * self.zoom, self.doc.height * self.zoom)

    def widget_to_image(self, pt):
        return QPointF((pt.x() - self.offset.x()) / self.zoom,
                       (pt.y() - self.offset.y()) / self.zoom)

    def fit_to_screen(self):
        margin = 40
        aw = max(50, self.width() - margin * 2)
        ah = max(50, self.height() - margin * 2)
        self.zoom = max(0.02, min(aw / self.doc.width, ah / self.doc.height, 8.0))
        self.offset = QPointF((self.width() - self.doc.width * self.zoom) / 2,
                              (self.height() - self.doc.height * self.zoom) / 2)
        self.zoom_changed.emit(self.zoom)
        self.update()

    def set_zoom(self, z, anchor=None):
        z = max(0.02, min(32.0, z))
        if anchor is None:
            anchor = QPointF(self.width() / 2, self.height() / 2)
        img_pt = self.widget_to_image(anchor)
        self.zoom = z
        self.offset = QPointF(anchor.x() - img_pt.x() * z,
                              anchor.y() - img_pt.y() * z)
        self.zoom_changed.emit(self.zoom)
        self.update()

    def set_preview(self, img):
        self.preview = img
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#12141a"))
        rect = self.image_rect()

        p.save()
        p.setClipRect(rect)
        p.fillRect(rect, QBrush(self._checker))
        img = self.preview if self.preview is not None else self.doc.composite()

        if self.state.split_view and self.doc.baseline is not None:
            base = self.doc.baseline
            p.drawImage(QRectF(rect.left(), rect.top(), rect.width() / 2, rect.height()),
                        base, QRectF(0, 0, base.width() / 2, base.height()))
            p.drawImage(QRectF(rect.left() + rect.width() / 2, rect.top(),
                               rect.width() / 2, rect.height()),
                        img, QRectF(img.width() / 2, 0, img.width() / 2, img.height()))
            p.setPen(QPen(QColor("#8B5CF6"), 2))
            p.drawLine(QPointF(rect.center().x(), rect.top()),
                       QPointF(rect.center().x(), rect.bottom()))
        else:
            if not self.weak:
                p.setRenderHint(QPainter.SmoothPixmapTransform, True)
            p.drawImage(rect, img)
        p.restore()

        if self.doc.selection is not None:
            self._draw_selection_outline(p, rect)

        if self._crop_rect is not None:
            p.setPen(QPen(QColor("#FF8A3D"), 1, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRect(self._crop_rect)

        p.setPen(QPen(QColor("#5b6273"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(rect)

        if self.state.show_grid and self.zoom > 0.15:
            p.setPen(QPen(QColor(255, 255, 255, 40), 1))
            step = 64
            x = rect.left()
            while x < rect.right():
                p.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                x += step * max(1.0, self.zoom)
            y = rect.top()
            while y < rect.bottom():
                p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
                y += step * max(1.0, self.zoom)

        if self.state.show_rulers:
            self._draw_rulers(p, rect)

        if self.state.tool in ("brush", "pencil", "eraser", "blur_tool", "sharpen_tool",
                               "dodge", "burn", "clone", "heal", "smudge", "color_replace") \
                and self.underMouse():
            pos = self.mapFromGlobal(self.cursor().pos())
            r = self.state.brush_size * self.zoom / 2
            p.setPen(QPen(QColor(255, 255, 255, 200), 1))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(pos), r, r)

    def _draw_selection_outline(self, p, rect):
        mask = self.doc.selection
        bm = QBitmap.fromImage(mask.convertToFormat(QImage.Format_Mono))
        region = QRegion(bm)
        p.setClipRect(rect)
        p.save()
        p.scale(self.zoom, self.zoom)
        p.translate(self.offset / self.zoom)
        p.setPen(QPen(QColor(255, 255, 255), 0.8 / self.zoom, Qt.DashLine))
        p.setBrush(Qt.NoBrush)
        for r in region.rects():
            p.drawRect(QRectF(r))
        p.restore()

    def _draw_rulers(self, p, rect):
        h = 18
        p.fillRect(QRectF(0, 0, self.width(), h), QColor("#202530"))
        p.fillRect(QRectF(0, 0, h, self.height()), QColor("#202530"))
        p.setPen(QColor("#A1A8B5"))
        f = p.font(); f.setPointSize(7); p.setFont(f)
        step_img = 100
        while step_img * self.zoom < 60:
            step_img *= 2
        x = int(max(0, (0 - rect.left()) / self.zoom))
        x = (x // step_img) * step_img
        while True:
            wx = self.offset.x() + x * self.zoom
            if wx > self.width():
                break
            if wx >= h:
                p.drawLine(QPointF(wx, h - 5), QPointF(wx, h))
                p.drawText(QPointF(wx + 2, h - 6), str(x))
            x += step_img
        y = int(max(0, (0 - rect.top()) / self.zoom))
        y = (y // step_img) * step_img
        while True:
            wy = self.offset.y() + y * self.zoom
            if wy > self.height():
                break
            if wy >= h:
                p.drawLine(QPointF(h - 5, wy), QPointF(h, wy))
                p.save(); p.translate(h - 6, wy + 2); p.rotate(-90)
                p.drawText(QPointF(0, 0), str(y)); p.restore()
            y += step_img

    def wheelEvent(self, e):
        factor = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self.set_zoom(self.zoom * factor, e.position())

    def mousePressEvent(self, e):
        pos = e.position()
        ip = self.widget_to_image(pos)
        x, y = int(ip.x()), int(ip.y())
        tool = self.state.tool

        if e.button() == Qt.MiddleButton or tool == "hand":
            self._panning = True
            self._pan_start = pos
            return

        if tool == "zoom":
            self.set_zoom(self.zoom * (1.25 if e.button() == Qt.LeftButton else 1 / 1.25), pos)
            return

        if e.button() != Qt.LeftButton:
            return

        if tool == "eyedropper":
            comp = self.doc.composite().convertToFormat(QImage.Format_RGBA8888)
            if 0 <= x < self.doc.width and 0 <= y < self.doc.height:
                c = QColor.fromRgba(comp.pixel(x, y))
                self.state.fg = c
                self.status.emit(f"Color: {c.name().upper()}")
            return

        if tool in ("marquee_rect", "marquee_ellipse", "crop"):
            self._sel_start = pos
            if tool == "crop":
                self._crop_rect = QRectF(pos, pos)
            return

        if tool == "lasso":
            self._lasso_points = [(pos.x(), pos.y())]
            return

        if tool == "magic_wand":
            layer = self.doc.active_layer()
            if layer is None:
                return
            mask = flood_fill_mask(layer.image, x, y, self.state.tolerance)
            self._set_selection(mask)
            return

        if tool in ("bucket", "color_replace"):
            layer = self.doc.active_layer()
            if layer is None or layer.locked:
                return
            mask = flood_fill_mask(layer.image, x, y, self.state.tolerance)
            before = layer.image.copy()
            p = QPainter(layer.image)
            p.setCompositionMode(QPainter.CompositionMode_Source)
            overlay = QImage(self.doc.width, self.doc.height,
                             QImage.Format_ARGB32_Premultiplied)
            overlay.fill(self.state.fg)
            p.setClipRegion(QRegion(QBitmap.fromImage(
                mask.convertToFormat(QImage.Format_Mono))))
            p.drawImage(0, 0, overlay)
            p.end()
            label = "Paint Bucket" if tool == "bucket" else "Color Replace"
            self.doc.commit_pixels(label, self.doc.active, before)
            self.doc.invalidate(); self.doc.changed.emit()
            self.update()
            return

        if tool == "text":
            dlg = TextDialog(self)
            if dlg.exec() == QDialog.Accepted:
                params = dlg.result_params(max(0, x), max(0, y))
                img = render_text_layer(params, self.doc.width, self.doc.height)
                layer = Layer(f"Text: {params['text'][:12]}", self.doc.width,
                              self.doc.height, img, kind="text", params=params)
                idx = self.doc.add_layer(layer)
                self.doc.push_custom("Add Text",
                                     lambda: self.doc.remove_layer(idx),
                                     lambda: None, 0)
                self._refresh_parent_layers()
            return

        if tool in ("brush", "pencil", "eraser"):
            layer = self.doc.active_layer()
            if layer is None or layer.locked:
                return
            self._drawing = True
            self._stroke_before = layer.image.copy()
            self._last_img_pos = ip
            self._paint_dab(ip)
            return

        if tool in ("blur_tool", "sharpen_tool", "dodge", "burn"):
            layer = self.doc.active_layer()
            if layer is None or layer.locked:
                return
            self._drawing = True
            self._stroke_before = layer.image.copy()
            self._apply_effect_dab(x, y)
            return

        if tool == "clone":
            layer = self.doc.active_layer()
            if layer is None or layer.locked:
                return
            if e.modifiers() & Qt.AltModifier:
                self.state.clone_source = QPointF(ip)
                self.state.clone_offset = None
                self.status.emit(f"Clone source set: ({int(ip.x())}, {int(ip.y())})")
                return
            if self.state.clone_source is None:
                self.status.emit("Alt+click first to set clone source")
                return
            self.state.clone_offset = QPointF(self.state.clone_source.x() - ip.x(),
                                              self.state.clone_source.y() - ip.y())
            self._drawing = True
            self._stroke_before = layer.image.copy()
            self._clone_anchor = QPointF(ip)
            self._do_clone(ip)
            return

        if tool == "heal":
            layer = self.doc.active_layer()
            if layer is None or layer.locked:
                return
            if e.modifiers() & Qt.AltModifier:
                self.state.clone_source = QPointF(ip)
                self.state.clone_offset = None
                self.status.emit(f"Heal source set: ({int(ip.x())}, {int(ip.y())})")
                return
            if self.state.clone_source is None:
                self.status.emit("Alt+click first to set heal source")
                return
            self._drawing = True
            self._stroke_before = layer.image.copy()
            self._do_heal(ip)
            return

        if tool == "smudge":
            layer = self.doc.active_layer()
            if layer is None or layer.locked:
                return
            self._drawing = True
            self._stroke_before = layer.image.copy()
            self._smudge_buf = layer.image.copy()
            self._smudge_pick = QPointF(ip)
            return

        if tool in ("move", "gradient", "shape", "line"):
            self._drawing = True
            layer = self.doc.active_layer()
            self._stroke_before = layer.image.copy() if layer else None
            self._shape_start = ip

    def mouseMoveEvent(self, e):
        pos = e.position()
        ip = self.widget_to_image(pos)
        self.cursor_moved.emit(int(ip.x()), int(ip.y()))

        if self._panning:
            delta = pos - self._pan_start
            self.offset += delta
            self._pan_start = pos
            self.update()
            return

        if self._sel_start is not None:
            r = QRectF(self._sel_start, pos).normalized()
            if self.state.tool == "crop":
                self._crop_rect = r
            else:
                self._rubber_rect = r
                self._apply_rubber_selection(r, self.state.tool == "marquee_ellipse")
            self.update()
            return

        if self._lasso_points:
            self._lasso_points.append((pos.x(), pos.y()))
            self.update()
            return

        if not self._drawing:
            self.update()
            return

        tool = self.state.tool
        if tool in ("brush", "pencil", "eraser"):
            self._stroke_line(self._last_img_pos or ip, ip)
            self._last_img_pos = ip
        elif tool in ("blur_tool", "sharpen_tool", "dodge", "burn"):
            self._apply_effect_dab(int(ip.x()), int(ip.y()))
        elif tool == "clone":
            self._do_clone(ip)
        elif tool == "heal":
            self._do_heal(ip)
        elif tool == "smudge":
            self._do_smudge(ip)
        elif tool == "move":
            if self._shape_start is not None:
                dx = int(ip.x() - self._shape_start.x())
                dy = int(ip.y() - self._shape_start.y())
                self._move_layer(dx, dy)
        else:
            self.update()

    def mouseReleaseEvent(self, e):
        pos = e.position()
        ip = self.widget_to_image(pos)
        tool = self.state.tool

        if self._panning:
            self._panning = False
            return

        if self._sel_start is not None:
            r = QRectF(self._sel_start, pos).normalized()
            self._sel_start = None
            if tool == "crop":
                if r.width() > 5 and r.height() > 5:
                    tl = self.widget_to_image(r.topLeft())
                    br = self.widget_to_image(r.bottomRight())
                    x = max(0, int(tl.x())); y = max(0, int(tl.y()))
                    w = max(1, int(br.x() - tl.x()))
                    h = max(1, int(br.y() - tl.y()))
                    self.doc.crop(x, y, w, h)
                    self._crop_rect = None
                    self.fit_to_screen()
            self.update()
            return

        if self._lasso_points:
            pts = self._lasso_points
            self._lasso_points = []
            if len(pts) > 2:
                self._lasso_select(pts)
            return

        if not self._drawing:
            return
        self._drawing = False

        if tool in ("brush", "pencil", "eraser", "blur_tool", "sharpen_tool", "dodge", "burn",
                    "clone", "heal", "smudge"):
            if self._stroke_before is not None:
                self.doc.commit_pixels(tool.capitalize(), self.doc.active, self._stroke_before)
                self.doc.invalidate(); self.doc.changed.emit()
            self._stroke_before = None
            self._smudge_buf = None
            return

        if tool == "gradient" and self._shape_start is not None:
            self._draw_gradient(self._shape_start, ip)
        elif tool in ("shape", "line") and self._shape_start is not None:
            self._draw_shape(self._shape_start, ip, tool == "line")
        elif tool == "move" and self._stroke_before is not None:
            self.doc.commit_pixels("Move", self.doc.active, self._stroke_before)
            self.doc.invalidate(); self.doc.changed.emit()
        self._shape_start = None
        self._stroke_before = None
        self.update()

    def _paint_dab(self, ip, painter=None):
        layer = self.doc.active_layer()
        if layer is None:
            return
        own = painter is None
        if own:
            painter = QPainter(layer.image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        tool = self.state.tool
        size = self.state.brush_size
        if tool == "pencil":
            size = max(1, size // 4)
        r = size / 2.0
        color = None
        if tool == "eraser":
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.setBrush(QColor(0, 0, 0, 255))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(ip, r, r)
        else:
            hard = max(0.0, min(1.0, self.state.brush_hardness / 100.0))
            grad = QRadialGradient(ip, r)
            color = self.state.fg
            a = int(255 * self.state.brush_flow / 100.0)
            color = QColor(color.red(), color.green(), color.blue(), a)
            grad.setColorAt(0.0, color)
            if hard > 0:
                grad.setColorAt(min(0.999, hard), color)
            edge = QColor(color); edge.setAlpha(0)
            grad.setColorAt(1.0, edge)
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.setOpacity(self.state.brush_opacity / 100.0)
            painter.drawEllipse(ip, r, r)
        if self.state.symmetry:
            mirrored = QPointF(self.doc.width - ip.x(), ip.y())
            if tool != "eraser":
                grad2 = QRadialGradient(mirrored, r)
                grad2.setColorAt(0.0, color)
                grad2.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
                painter.setBrush(QBrush(grad2))
            else:
                painter.setBrush(QColor(0, 0, 0, 255))
            painter.drawEllipse(mirrored, r, r)
        if own:
            painter.end()
            self.doc.invalidate()
            self.update()

    def _stroke_line(self, a, b):
        dist = math.hypot(b.x() - a.x(), b.y() - a.y())
        spacing = max(1.0, self.state.brush_size * self.state.brush_spacing / 100.0)
        steps = max(1, int(dist / spacing))
        layer = self.doc.active_layer()
        if layer is None:
            return
        painter = QPainter(layer.image)
        for i in range(1, steps + 1):
            t = i / steps
            pt = QPointF(a.x() + (b.x() - a.x()) * t, a.y() + (b.y() - a.y()) * t)
            self._paint_dab(pt, painter)
        painter.end()
        self.doc.invalidate()
        self.update()

    def _apply_effect_dab(self, x, y):
        layer = self.doc.active_layer()
        if layer is None:
            return
        r = int(self.state.brush_size / 2)
        w, h = layer.image.width(), layer.image.height()
        x0 = max(0, x - r); y0 = max(0, y - r)
        x1 = min(w, x + r + 1); y1 = min(h, y + r + 1)
        if x0 >= x1 or y0 >= y1:
            return
        region = layer.image.copy(x0, y0, x1 - x0, y1 - y0)
        tool = self.state.tool
        if tool == "blur_tool":
            eff = eng_blur(region, max(1.0, r / 3.0))
        elif tool == "sharpen_tool":
            eff = eng_sharpen(region, 1.2)
        elif tool == "dodge":
            eff = eng_adjust(region, brightness=18)
        else:
            eff = eng_adjust(region, brightness=-18)

        p = QPainter(layer.image)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        grad = QRadialGradient(QPointF(x, y), r)
        grad.setColorAt(0.0, QColor(255, 255, 255, 220))
        grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        eff_masked = eff.copy()
        pm = QPainter(eff_masked)
        pm.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        pm.setBrush(QBrush(grad))
        pm.setPen(Qt.NoPen)
        pm.drawRect(0, 0, eff_masked.width(), eff_masked.height())
        pm.end()
        p.drawImage(x0, y0, eff_masked)
        p.end()
        self.doc.invalidate()
        self.update()

    def _do_clone(self, ip):
        layer = self.doc.active_layer()
        if layer is None or self.state.clone_offset is None:
            return
        r = int(self.state.brush_size / 2)
        w, h = layer.image.width(), layer.image.height()
        src = QPointF(ip.x() + self.state.clone_offset.x(),
                      ip.y() + self.state.clone_offset.y())
        x0 = int(src.x()) - r; y0 = int(src.y()) - r
        if x0 < 0 or y0 < 0 or x0 + 2 * r > w or y0 + 2 * r > h:
            return
        patch = layer.image.copy(x0, y0, 2 * r, 2 * r)
        grad = QRadialGradient(QPointF(r, r), r)
        grad.setColorAt(0.0, QColor(255, 255, 255, 230))
        grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        pm = QPainter(patch)
        pm.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        pm.setBrush(QBrush(grad)); pm.setPen(Qt.NoPen)
        pm.drawRect(0, 0, patch.width(), patch.height())
        pm.end()
        p = QPainter(layer.image)
        p.setOpacity(self.state.brush_opacity / 100.0)
        p.drawImage(int(ip.x()) - r, int(ip.y()) - r, patch)
        p.setOpacity(1.0)
        p.end()
        self.doc.invalidate()
        self.update()

    def _do_heal(self, ip):
        layer = self.doc.active_layer()
        if layer is None or self.state.clone_offset is None:
            return
        r = max(1, int(self.state.brush_size / 2))
        w, h = layer.image.width(), layer.image.height()
        src = QPointF(ip.x() + self.state.clone_offset.x(),
                      ip.y() + self.state.clone_offset.y())
        x0 = int(src.x()) - r; y0 = int(src.y()) - r
        if x0 < 0 or y0 < 0 or x0 + 2 * r > w or y0 + 2 * r > h:
            return
        patch = layer.image.copy(x0, y0, 2 * r, 2 * r)
        target = layer.image.copy(int(ip.x()) - r, int(ip.y()) - r, 2 * r, 2 * r)
        patch_avg = self._avg_luma(patch)
        target_avg = self._avg_luma(target)
        delta = target_avg - patch_avg
        patch = eng_adjust(patch, brightness=delta / 2.55)
        grad = QRadialGradient(QPointF(r, r), r)
        grad.setColorAt(0.0, QColor(255, 255, 255, 230))
        grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        pm = QPainter(patch)
        pm.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        pm.setBrush(QBrush(grad)); pm.setPen(Qt.NoPen)
        pm.drawRect(0, 0, patch.width(), patch.height())
        pm.end()
        p = QPainter(layer.image)
        p.setOpacity(self.state.brush_opacity / 100.0)
        p.drawImage(int(ip.x()) - r, int(ip.y()) - r, patch)
        p.setOpacity(1.0)
        p.end()
        self.doc.invalidate()
        self.update()

    def _avg_luma(self, img):
        small = img.scaled(16, 16, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        data, w, h = qimg_rgba_bytes(small)
        total = 0.0
        n = 0
        for i in range(0, len(data), 4):
            if data[i + 3] > 0:
                total += data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114
                n += 1
        return total / max(1, n)

    def _do_smudge(self, ip):
        layer = self.doc.active_layer()
        if layer is None or self._smudge_buf is None:
            return
        r = max(1, int(self.state.brush_size / 2))
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.Antialiasing, True)
        grad = QRadialGradient(ip, r)
        grad.setColorAt(0.0, QColor(255, 255, 255, 180))
        grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        prev = self._smudge_pick or ip
        x0 = int(prev.x()) - r; y0 = int(prev.y()) - r
        w, h = layer.image.width(), layer.image.height()
        if 0 <= x0 and 0 <= y0 and x0 + 2 * r <= w and y0 + 2 * r <= h:
            patch = layer.image.copy(x0, y0, 2 * r, 2 * r)
            pm = QPainter(patch)
            pm.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            pm.setBrush(QBrush(grad)); pm.setPen(Qt.NoPen)
            pm.drawRect(0, 0, patch.width(), patch.height())
            pm.end()
            p.drawImage(int(ip.x()) - r, int(ip.y()) - r, patch)
        p.setOpacity(1.0)
        p.end()
        self._smudge_pick = QPointF(ip)
        self.doc.invalidate()
        self.update()

    def _move_layer(self, dx, dy):
        layer = self.doc.active_layer()
        if layer is None or self._stroke_before is None:
            return
        new_img = QImage(self.doc.width, self.doc.height,
                         QImage.Format_ARGB32_Premultiplied)
        new_img.fill(Qt.transparent)
        p = QPainter(new_img)
        p.drawImage(dx, dy, self._stroke_before)
        p.end()
        layer.image = new_img
        self.doc.invalidate()
        self.update()

    def _draw_gradient(self, a, b):
        layer = self.doc.active_layer()
        if layer is None or self._stroke_before is None:
            return
        p = QPainter(layer.image)
        grad = QLinearGradient(a, b)
        grad.setColorAt(0.0, self.state.fg)
        grad.setColorAt(1.0, self.state.bg)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(grad))
        p.drawRect(0, 0, self.doc.width, self.doc.height)
        p.end()
        self.doc.commit_pixels("Gradient", self.doc.active, self._stroke_before)
        self.doc.invalidate(); self.doc.changed.emit()
        self.update()

    def _draw_shape(self, a, b, is_line):
        layer = self.doc.active_layer()
        if layer is None or self._stroke_before is None:
            return
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.state.fg, max(1, self.state.brush_size // 4))
        p.setPen(pen)
        fill = QColor(self.state.fg); fill.setAlpha(60)
        p.setBrush(QBrush(fill))
        r = QRectF(a, b).normalized()
        if is_line:
            p.setBrush(Qt.NoBrush)
            p.drawLine(a, b)
        elif QApplication.keyboardModifiers() & Qt.ShiftModifier:
            p.drawEllipse(r)
        else:
            p.drawRect(r)
        p.end()
        self.doc.commit_pixels("Shape", self.doc.active, self._stroke_before)
        self.doc.invalidate(); self.doc.changed.emit()
        self.update()

    def _apply_rubber_selection(self, rect, ellipse):
        tl = self.widget_to_image(rect.topLeft())
        br = self.widget_to_image(rect.bottomRight())
        x0 = max(0, min(self.doc.width, int(tl.x())))
        y0 = max(0, min(self.doc.height, int(tl.y())))
        x1 = max(0, min(self.doc.width, int(br.x())))
        y1 = max(0, min(self.doc.height, int(br.y())))
        mask = QImage(self.doc.width, self.doc.height, QImage.Format_Grayscale8)
        mask.fill(0)
        p = QPainter(mask)
        p.setPen(Qt.NoPen); p.setBrush(QColor(255, 255, 255))
        if ellipse:
            p.drawEllipse(QRect(x0, y0, x1 - x0, y1 - y0))
        else:
            p.drawRect(x0, y0, x1 - x0, y1 - y0)
        p.end()
        self._set_selection(mask)

    def _lasso_select(self, points):
        mask = QImage(self.doc.width, self.doc.height, QImage.Format_Grayscale8)
        mask.fill(0)
        p = QPainter(mask)
        p.setPen(Qt.NoPen); p.setBrush(QColor(255, 255, 255))
        poly = QPolygonF([self.widget_to_image(QPointF(x, y)) for x, y in points])
        p.drawPolygon(poly)
        p.end()
        self._set_selection(mask)

    def _set_selection(self, mask):
        if mask is None:
            self.doc.selection = None
            self.update()
            return
        if self.state.feather > 0:
            mask = eng_blur(mask, self.state.feather)
        mods = QApplication.keyboardModifiers()
        cur = self.doc.selection
        if cur is None or (not (mods & (Qt.ShiftModifier | Qt.AltModifier))):
            self.doc.selection = mask
        elif mods & Qt.ShiftModifier:
            combined = cur.copy()
            p = QPainter(combined)
            p.setCompositionMode(QPainter.CompositionMode_Lighten)
            p.drawImage(0, 0, mask)
            p.end()
            self.doc.selection = combined
        elif mods & Qt.AltModifier:
            combined = cur.copy()
            p = QPainter(combined)
            p.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            p.drawImage(0, 0, mask)
            p.end()
            self.doc.selection = combined
        self.update()

    def _refresh_parent_layers(self):
        w = self.parent()
        while w is not None and not hasattr(w, "_refresh_layers"):
            w = w.parent() if hasattr(w, "parent") else None
        if w is not None and hasattr(w, "_refresh_layers"):
            try:
                w._refresh_layers()
            except Exception:
                pass


# ──────────────────── الأيقونة الاحترافية (حرف D بأسلوب حديث) ────────────────────
def make_app_icon(size: int = 256) -> QIcon:
    """
    لوجو التطبيق: أيقونة مسطحة وحديثة بحرف D أبيض على خلفية متدرجة.
    مصممة لتكون واضحة ومتناسقة مع أيقونات نظام التشغيل الحديثة.
    """
    render_size = 512
    img = QImage(render_size, render_size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)

    # ── 1. الخلفية: مربع بحواف دائرية (Squircle) ──
    margin = render_size * 0.06
    rect = QRectF(margin, margin,
                  render_size - 2 * margin, render_size - 2 * margin)
    radius = render_size * 0.24  # حواف دائرية مثل أيقونات Windows 11
    
    bg_path = QPainterPath()
    bg_path.addRoundedRect(rect, radius, radius)

    # تدرج لوني حديث (Cyan إلى Indigo/Purple)
    bg_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    bg_grad.setColorAt(0.0, QColor("#00E5FF"))  # Cyan
    bg_grad.setColorAt(1.0, QColor("#7C4DFF"))  # Indigo/Purple
    p.fillPath(bg_path, QBrush(bg_grad))

    # ── 2. حرف D الأبيض الناصع ──
    font = QFont()
    # استخدام خطوط عريضة جداً وواضحة
    font.setFamilies(["Segoe UI Black", "Arial Black", "Impact", "Arial"])
    font.setPixelSize(int(render_size * 0.72))
    font.setWeight(QFont.Black)
    font.setBold(True)

    d_path = QPainterPath()
    d_path.addText(QPointF(0, 0), font, "D")

    # توسيط الحرف بدقة في منتصف المربع
    bbox = d_path.boundingRect()
    d_path.translate(
        (render_size - bbox.width()) / 2 - bbox.left(),
        (render_size - bbox.height()) / 2 - bbox.top()
    )

    # رسم الحرف باللون الأبيض الصافي
    p.fillPath(d_path, QColor("#FFFFFF"))

    p.end()

    # تصغير الصورة إلى الحجم المطلوب
    return QIcon(QPixmap.fromImage(
        img.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    ))


# ──────────────────── MainWindow ────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings(ORG, ORG)
        self.state = AppState()
        self.docs: List[Document] = []
        self._ui_lock = False

        self.setWindowTitle(T("app_title"))
        self.resize(1280, 800)
        self.setWindowIcon(make_app_icon(256))

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_doc)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._build_docks()
        self._build_status()
        self._apply_theme()

        if self.settings.value("lang", "ar") == "ar":
            QApplication.setLayoutDirection(Qt.RightToLeft)
        else:
            QApplication.setLayoutDirection(Qt.LeftToRight)

        self.new_document(1280, 720, "Untitled-1")

    def templates_dialog(self):
        dlg = QDialog(self); dlg.setWindowTitle("New Project")
        dlg.resize(620, 480)
        outer = QVBoxLayout(dlg)
        outer.addWidget(QLabel("<h2>Dragon Pixel Studio</h2><p>CREATE WITHOUT LIMITS.</p>"))
        tabs = QTabWidget()

        presets_w = QWidget(); pv = QVBoxLayout(presets_w)
        lst = QListWidget()
        PRESETS = [
            ("Custom", 1280, 720),
            ("YouTube Thumbnail", 1280, 720),
            ("YouTube Banner", 2560, 1440),
            ("Instagram Post", 1080, 1080),
            ("Instagram Story", 1080, 1920),
            ("TikTok Cover", 1080, 1920),
            ("Facebook Post", 1200, 630),
            ("Website Banner", 1920, 600),
            ("Logo Canvas", 1000, 1000),
            ("Business Card", 1050, 600),
            ("Poster A3", 2480, 3508),
            ("Gaming Wallpaper", 2560, 1440),
        ]
        for name, w, h in PRESETS:
            it = QListWidgetItem(f"{name}  —  {w}×{h}")
            it.setData(Qt.UserRole, (w, h))
            lst.addItem(it)
        pv.addWidget(lst)

        custom_w = QWidget(); cv = QFormLayout(custom_w)
        w_spin = QSpinBox(); w_spin.setRange(1, 20000); w_spin.setValue(1280)
        h_spin = QSpinBox(); h_spin.setRange(1, 20000); h_spin.setValue(720)
        bg_combo = QComboBox(); bg_combo.addItems(["Transparent", "White", "Black"])
        cv.addRow("Width", w_spin)
        cv.addRow("Height", h_spin)
        cv.addRow("Background", bg_combo)

        tabs.addTab(presets_w, "Templates")
        tabs.addTab(custom_w, "Custom")
        outer.addWidget(tabs)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        outer.addWidget(bb)

        if dlg.exec() == QDialog.Accepted:
            if tabs.currentIndex() == 0 and lst.currentItem() is not None:
                w, h = lst.currentItem().data(Qt.UserRole)
                bg = "Transparent"
            else:
                w, h = w_spin.value(), h_spin.value()
                bg = bg_combo.currentText()
            self.new_document(w, h, background=bg)

    def _act(self, key, slot, shortcut=None, checkable=False):
        a = QAction(T(key), self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.setCheckable(checkable)
        if checkable:
            a.toggled.connect(slot)
        else:
            a.triggered.connect(slot)
        return a

    def _build_actions(self):
        self.act_new = self._act("new", self.new_document_dialog, "Ctrl+N")
        self.act_open = self._act("open", self.open_file, "Ctrl+O")
        self.act_save = self._act("save", self.save_file, "Ctrl+S")
        self.act_save_as = self._act("save_as", self.save_file_as, "Ctrl+Shift+S")
        self.act_export = self._act("export", self.export_file, "Ctrl+Shift+E")
        self.act_export_layers = self._act("export_layers", self.export_layers)
        self.act_quit = self._act("quit", self.close, "Ctrl+Q")

        self.act_undo = self._act("undo", self.undo, "Ctrl+Z")
        self.act_redo = self._act("redo", self.redo, "Ctrl+Y")
        self.act_prefs = self._act("prefs", self.show_settings)

        self.act_img_size = self._act("resize_image", self.image_size_dialog)
        self.act_canvas_size = self._act("resize_canvas", self.canvas_size_dialog)
        self.act_rot_cw = self._act("rot_cw", lambda: self._doc_op(lambda d: d.rotate(1)))
        self.act_rot_ccw = self._act("rot_ccw", lambda: self._doc_op(lambda d: d.rotate(3)))
        self.act_rot_180 = self._act("rot_180", lambda: self._doc_op(lambda d: d.rotate(2)))
        self.act_flip_h = self._act("flip_h", lambda: self._doc_op(lambda d: d.flip(True)))
        self.act_flip_v = self._act("flip_v", lambda: self._doc_op(lambda d: d.flip(False)))
        self.act_crop_sel = self._act("crop_sel", self.crop_to_selection)

        self.act_new_layer = self._act("new_layer", self.add_layer, "Ctrl+Shift+N")
        self.act_dup_layer = self._act("dup_layer", self.duplicate_layer, "Ctrl+J")
        self.act_del_layer = self._act("del_layer", self.delete_layer)
        self.act_merge_down = self._act("merge_down", lambda: self._doc_op(lambda d: d.merge_down()))
        self.act_flatten = self._act("flatten", lambda: self._doc_op(lambda d: d.flatten()))
        self.act_add_mask = self._act("add_mask", self.add_mask)
        self.act_del_mask = self._act("del_mask", self.remove_mask)
        self.act_inv_mask = self._act("inv_mask", self.invert_mask)
        self.act_apply_mask = self._act("apply_mask", self.apply_mask)
        self.act_layer_style = self._act("layer_style", self.layer_style_dialog)

        self.act_sel_all = self._act("sel_all", self.select_all, "Ctrl+A")
        self.act_deselect = self._act("deselect", self.deselect, "Ctrl+D")
        self.act_inv_sel = self._act("inv_sel", self.invert_selection, "Ctrl+Shift+I")
        self.act_feather = self._act("feather", self.feather_selection)
        self.act_expand = self._act("expand", lambda: self.grow_selection(1))
        self.act_contract = self._act("contract", lambda: self.grow_selection(-1))
        self.act_remove_bg = self._act("remove_bg", self.remove_background)

        self.act_bc = self._act("brightness_contrast", self.adjust_brightness_contrast)
        self.act_hs = self._act("hue_sat", self.adjust_hue_saturation)
        self.act_auto_contrast = self._act("auto_contrast", self.auto_contrast)
        self.act_invert = self._act("invert_colors",
                                    lambda: self.filter_simple("Invert", eng_invert), "Ctrl+I")
        self.act_gray = self._act("grayscale",
                                  lambda: self.filter_simple("Grayscale", eng_grayscale))
        self.act_sepia = self._act("sepia", lambda: self.filter_simple("Sepia", eng_sepia))

        self.act_gauss = self._act("gaussian_blur", lambda: self.dialog_blur("gaussian"))
        self.act_box = self._act("box_blur", lambda: self.dialog_blur("box"))
        self.act_sharpen = self._act("sharpen", self.dialog_sharpen)
        self.act_emboss = self._act("emboss", lambda: self.filter_simple("Emboss", eng_emboss))
        self.act_edges = self._act("find_edges", lambda: self.filter_simple("Find Edges", eng_find_edges))
        self.act_pixelate = self._act("pixelate", self.dialog_pixelate)
        self.act_noise = self._act("noise", self.dialog_noise)
        self.act_vignette = self._act("vignette", self.dialog_vignette)
        self.act_posterize = self._act("posterize", self.dialog_posterize)
        self.act_threshold = self._act("threshold", self.dialog_threshold)
        self.act_motion_blur = self._act("motion_blur", self.dialog_motion_blur)
        self.act_radial_blur = self._act("radial_blur", self.dialog_radial_blur)
        self.act_levels = self._act("levels", self.dialog_levels)
        self.act_color_balance = self._act("color_balance", self.dialog_color_balance)
        self.act_photo_filter = self._act("photo_filter", self.dialog_photo_filter)
        self.act_high_pass = self._act("high_pass", self.dialog_high_pass)
        self.act_median = self._act("median", self.dialog_median)

        self.act_zoom_in = self._act("zoom_in", lambda: self._zoom(1.25), "Ctrl++")
        self.act_zoom_out = self._act("zoom_out", lambda: self._zoom(1 / 1.25), "Ctrl+-")
        self.act_fit = self._act("fit", lambda: self._canvas_call("fit_to_screen"), "Ctrl+0")
        self.act_actual = self._act("actual", lambda: self._canvas_call("set_zoom", 1.0), "Ctrl+1")
        self.act_rulers = self._act("rulers", self.toggle_rulers, checkable=True)
        self.act_rulers.setChecked(True)
        self.act_grid = self._act("grid", self.toggle_grid, checkable=True)
        self.act_fullscreen = self._act("fullscreen", self.toggle_fullscreen, "F11")
        self.act_split = self._act("split", self.toggle_split, checkable=True)
        self.act_templates = self._act("templates", self.templates_dialog, "Ctrl+Shift+N")

        self.act_about = self._act("about", self.show_about)

        self.act_copy = QAction(T("copy"), self); self.act_copy.setShortcut("Ctrl+C")
        self.act_paste = QAction(T("paste"), self); self.act_paste.setShortcut("Ctrl+V")
        self.act_cut = QAction(T("cut"), self); self.act_cut.setShortcut("Ctrl+X")
        self.act_paste_layer = QAction(T("paste_as_layer"), self)
        self.act_paste_layer.setShortcut("Ctrl+Shift+V")
        self.act_copy.triggered.connect(self.copy_selection)
        self.act_cut.triggered.connect(self.cut_selection)
        self.act_paste.triggered.connect(self.paste_selection)
        self.act_paste_layer.triggered.connect(lambda: self.paste_selection(as_new_layer=True))
        self.addAction(self.act_copy)
        self.addAction(self.act_cut)
        self.addAction(self.act_paste)
        self.addAction(self.act_paste_layer)

        self.tool_actions = {}
        self._build_tool_actions()

    def _build_tool_actions(self):
        for tid, en, ar, sc, impl, glyph in TOOLS:
            icon = self._make_icon(glyph)
            a = QAction(icon, f"{en} / {ar}", self)
            a.setCheckable(True)
            a.setToolTip(f"{en} / {ar}" + (f"  ({sc})" if sc else ""))
            if not impl:
                a.setEnabled(False)
                a.setToolTip(f"{en} / {ar} — not implemented")
            a.triggered.connect(lambda _=False, t=tid: self.set_tool(t))
            self.tool_actions[tid] = a

    def _make_icon(self, glyph):
        pm = QPixmap(24, 24)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(QColor("#F3F4F6"))
        f = QFont(); f.setPointSize(13); p.setFont(f)
        p.drawText(pm.rect(), Qt.AlignCenter, glyph)
        p.end()
        return QIcon(pm)

    def _build_menus(self):
        mb = self.menuBar()
        m = mb.addMenu(T("file"))
        for a in (self.act_new, self.act_templates, self.act_open):
            m.addAction(a)
        self.recent_menu = m.addMenu(T("recent"))
        self._refresh_recent()
        m.addSeparator()
        for a in (self.act_save, self.act_save_as, self.act_export, self.act_export_layers):
            m.addAction(a)
        m.addSeparator()
        m.addAction(self.act_quit)

        m = mb.addMenu(T("edit"))
        for a in (self.act_undo, self.act_redo):
            m.addAction(a)
        m.addSeparator()
        for a in (self.act_copy, self.act_cut, self.act_paste, self.act_paste_layer):
            m.addAction(a)
        m.addSeparator()
        m.addAction(self.act_prefs)

        m = mb.addMenu(T("image"))
        for a in (self.act_img_size, self.act_canvas_size):
            m.addAction(a)
        m.addSeparator()
        for a in (self.act_rot_cw, self.act_rot_ccw, self.act_rot_180,
                  self.act_flip_h, self.act_flip_v, self.act_crop_sel):
            m.addAction(a)

        m = mb.addMenu(T("layer"))
        for a in (self.act_new_layer, self.act_dup_layer, self.act_del_layer):
            m.addAction(a)
        m.addSeparator()
        for a in (self.act_merge_down, self.act_flatten, self.act_layer_style):
            m.addAction(a)
        m.addSeparator()
        for a in (self.act_add_mask, self.act_inv_mask, self.act_apply_mask, self.act_del_mask):
            m.addAction(a)

        m = mb.addMenu(T("select"))
        for a in (self.act_sel_all, self.act_deselect, self.act_inv_sel):
            m.addAction(a)
        m.addSeparator()
        for a in (self.act_feather, self.act_expand, self.act_contract, self.act_remove_bg):
            m.addAction(a)

        m = mb.addMenu(T("filter"))
        for a in (self.act_gauss, self.act_box, self.act_sharpen):
            m.addAction(a)
        m.addSeparator()
        for a in (self.act_emboss, self.act_edges, self.act_pixelate, self.act_noise,
                  self.act_vignette, self.act_posterize, self.act_threshold):
            m.addAction(a)
        m.addSeparator()
        for a in (self.act_motion_blur, self.act_radial_blur, self.act_high_pass,
                  self.act_median, self.act_levels, self.act_color_balance,
                  self.act_photo_filter):
            m.addAction(a)

        m = mb.addMenu(T("colors"))
        for a in (self.act_bc, self.act_hs, self.act_auto_contrast, self.act_invert,
                  self.act_gray, self.act_sepia):
            m.addAction(a)

        m = mb.addMenu(T("view"))
        for a in (self.act_zoom_in, self.act_zoom_out, self.act_fit, self.act_actual):
            m.addAction(a)
        m.addSeparator()
        for a in (self.act_rulers, self.act_grid, self.act_split, self.act_fullscreen):
            m.addAction(a)

        self.window_menu = mb.addMenu(T("window"))
        m = mb.addMenu(T("help"))
        m.addAction(self.act_about)

    def _refresh_recent(self):
        self.recent_menu.clear()
        recent = self.settings.value("recent", [])
        if recent is None:
            recent = []
        elif isinstance(recent, str):
            recent = [recent]
        elif not isinstance(recent, (list, tuple)):
            recent = [str(recent)]
        shown = 0
        for path in recent:
            if not isinstance(path, str) or not path:
                continue
            a = QAction(os.path.basename(path), self)
            a.triggered.connect(lambda _=False, p=path: self.open_path(p))
            self.recent_menu.addAction(a)
            shown += 1
            if shown >= 10:
                break
        if shown == 0:
            a = QAction("—", self); a.setEnabled(False)
            self.recent_menu.addAction(a)

    def _add_recent(self, path):
        recent = self.settings.value("recent", [])
        if recent is None:
            recent = []
        elif isinstance(recent, str):
            recent = [recent]
        elif not isinstance(recent, (list, tuple)):
            recent = [str(recent)]
        recent = [p for p in recent if p != path]
        recent.insert(0, path)
        self.settings.setValue("recent", recent[:10])
        self._refresh_recent()

    def _build_toolbar(self):
        tb = QToolBar("Tools")
        tb.setOrientation(Qt.Vertical)
        tb.setIconSize(QSize(22, 22))
        tb.setMovable(False)
        self.addToolBar(Qt.LeftToolBarArea, tb)
        for tid, *_ in TOOLS:
            tb.addAction(self.tool_actions[tid])
            if tid in ("crop", "eraser", "color_replace", "line"):
                tb.addSeparator()
        self.tool_actions["move"].setChecked(True)
        self.toolbar = tb

    def _dock(self, title, widget, area=Qt.RightDockWidgetArea):
        d = QDockWidget(title, self)
        d.setObjectName(title); d.setWidget(widget)
        d.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(area, d)
        self.window_menu.addAction(d.toggleViewAction())
        return d

    def _build_docks(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(6, 6, 6, 6)
        row = QHBoxLayout()
        self.blend_combo = QComboBox(); self.blend_combo.addItems(BLEND_MODES)
        self.blend_combo.currentTextChanged.connect(self._on_blend_changed)
        self.opacity_slider = QSlider(Qt.Horizontal); self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        row.addWidget(QLabel(T("blend")))
        row.addWidget(self.blend_combo)
        lay.addLayout(row)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel(T("opacity")))
        row2.addWidget(self.opacity_slider)
        lay.addLayout(row2)
        self.layer_list = QListWidget()
        self.layer_list.itemChanged.connect(self._on_layer_item_changed)
        self.layer_list.currentRowChanged.connect(self._on_layer_row_changed)
        lay.addWidget(self.layer_list)
        btns = QHBoxLayout()
        for label, fn in (("+", self.add_layer), ("⧉", self.duplicate_layer),
                          ("🗑", self.delete_layer), ("▼", lambda: self._doc_op(lambda d: d.merge_down())),
                          ("◐", self.add_mask), ("✦", self.layer_style_dialog)):
            b = QToolButton(); b.setText(label); b.clicked.connect(fn); btns.addWidget(b)
        lay.addLayout(btns)
        self.dock_layers = self._dock(T("layers"), w)

        w = QWidget(); lay = QVBoxLayout(w)
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self._on_history_clicked)
        lay.addWidget(self.history_list)
        self.dock_history = self._dock(T("history"), w)

        w = QWidget(); lay = QVBoxLayout(w)
        self.fg_btn = QPushButton(T("fg")); self.fg_btn.clicked.connect(lambda: self._pick_color("fg"))
        self.bg_btn = QPushButton(T("bg")); self.bg_btn.clicked.connect(lambda: self._pick_color("bg"))
        lay.addWidget(self.fg_btn); lay.addWidget(self.bg_btn); lay.addStretch()
        self.dock_color = self._dock(T("color"), w)
        self._update_color_buttons()

        w = QWidget(); lay = QFormLayout(w)
        self.size_spin = QSpinBox(); self.size_spin.setRange(1, 800); self.size_spin.setValue(self.state.brush_size)
        self.size_spin.valueChanged.connect(self._on_brush_change)
        self.hard_spin = QSpinBox(); self.hard_spin.setRange(0, 100); self.hard_spin.setValue(self.state.brush_hardness)
        self.hard_spin.valueChanged.connect(self._on_brush_change)
        self.op_spin = QSpinBox(); self.op_spin.setRange(0, 100); self.op_spin.setValue(self.state.brush_opacity)
        self.op_spin.valueChanged.connect(self._on_brush_change)
        self.flow_spin = QSpinBox(); self.flow_spin.setRange(1, 100); self.flow_spin.setValue(self.state.brush_flow)
        self.flow_spin.valueChanged.connect(self._on_brush_change)
        self.spacing_spin = QSpinBox(); self.spacing_spin.setRange(1, 200); self.spacing_spin.setValue(self.state.brush_spacing)
        self.spacing_spin.valueChanged.connect(self._on_brush_change)
        self.tol_spin = QSpinBox(); self.tol_spin.setRange(0, 255); self.tol_spin.setValue(self.state.tolerance)
        self.tol_spin.valueChanged.connect(lambda v: setattr(self.state, "tolerance", v))
        self.sym_check = QCheckBox(T("symmetry"))
        self.sym_check.toggled.connect(lambda v: setattr(self.state, "symmetry", v))
        self.dodge_mode = QComboBox(); self.dodge_mode.addItems(["Shadows", "Midtones", "Highlights"])
        self.dodge_mode.currentTextChanged.connect(lambda v: setattr(self.state, "dodge_mode", v))
        lay.addRow(T("size"), self.size_spin)
        lay.addRow(T("hardness"), self.hard_spin)
        lay.addRow(T("opacity"), self.op_spin)
        lay.addRow(T("flow"), self.flow_spin)
        lay.addRow(T("spacing"), self.spacing_spin)
        lay.addRow(T("tolerance"), self.tol_spin)
        lay.addRow(self.sym_check)
        lay.addRow("Dodge/Burn", self.dodge_mode)
        self.dock_brush = self._dock(T("brushes"), w)

        w = QWidget(); lay = QVBoxLayout(w)
        for label, fn in ((T("brightness_contrast"), self.adjust_brightness_contrast),
                          (T("hue_sat"), self.adjust_hue_saturation),
                          (T("auto_contrast"), self.auto_contrast),
                          (T("levels"), self.dialog_levels),
                          (T("color_balance"), self.dialog_color_balance),
                          (T("photo_filter"), self.dialog_photo_filter),
                          (T("invert_colors"), lambda: self.filter_simple("Invert", eng_invert)),
                          (T("grayscale"), lambda: self.filter_simple("Grayscale", eng_grayscale)),
                          (T("sepia"), lambda: self.filter_simple("Sepia", eng_sepia))):
            b = QPushButton(label); b.clicked.connect(fn); lay.addWidget(b)
        lay.addStretch()
        self.dock_adj = self._dock(T("adjustments"), w)

        w = QWidget(); lay = QVBoxLayout(w)
        self.zoom_label = QLabel("100%")
        self.zoom_slider = QSlider(Qt.Horizontal); self.zoom_slider.setRange(2, 800); self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(lambda v: self._canvas_call("set_zoom", v / 100.0))
        lay.addWidget(self.zoom_label); lay.addWidget(self.zoom_slider); lay.addStretch()
        self.dock_nav = self._dock(T("navigator"), w)

        self.tabifyDockWidget(self.dock_layers, self.dock_history)
        self.dock_layers.raise_()

    def _build_status(self):
        sb = QStatusBar(); self.setStatusBar(sb)
        self.lbl_dim = QLabel("—")
        self.lbl_zoom = QLabel("100%")
        self.lbl_pos = QLabel("0, 0")
        self.lbl_msg = QLabel(T("ready"))
        self.lbl_engine = QLabel(f"Engine: {'Rust ' + ENGINE_VERSION if ENGINE_OK else 'Python (fallback)'}")
        self.progress = QProgressBar(); self.progress.setRange(0, 100)
        self.progress.setFixedWidth(140); self.progress.setVisible(False)
        for wdg in (self.lbl_dim, self.lbl_zoom, self.lbl_pos, self.lbl_msg,
                    self.lbl_engine, self.progress):
            sb.addPermanentWidget(wdg)

    def _apply_theme(self):
        theme = self.settings.value("theme", "dark")
        accent = self.settings.value("accent", "#FF4D4D")
        if theme == "dark":
            bg, bg2, fg, fg2 = "#171A22", "#202530", "#F3F4F6", "#A1A8B5"
        else:
            bg, bg2, fg, fg2 = "#F3F4F6", "#FFFFFF", "#171A22", "#4B5563"
        self.setStyleSheet(f"""
        QMainWindow, QWidget {{ background: {bg}; color: {fg}; font-family: 'Segoe UI', 'Tahoma', sans-serif; }}
        QMenuBar {{ background: {bg2}; }}
        QMenuBar::item:selected {{ background: {accent}; color: #fff; border-radius:4px; }}
        QMenu {{ background: {bg2}; border: 1px solid #333a49; }}
        QMenu::item:selected {{ background: {accent}; color: #fff; }}
        QToolBar {{ background: {bg2}; border: none; padding: 4px; spacing: 4px; }}
        QToolButton {{ background: transparent; border-radius: 6px; padding: 4px; color: {fg}; }}
        QToolButton:hover {{ background: rgba(139,92,246,0.25); }}
        QToolButton:checked {{ background: {accent}; color: #fff; }}
        QDockWidget {{ color: {fg}; }}
        QDockWidget::title {{ background: {bg2}; padding: 6px; border-radius: 4px; }}
        QListWidget {{ background: {bg2}; border: 1px solid #2c3340; border-radius: 6px; }}
        QListWidget::item:selected {{ background: {accent}; color: #fff; }}
        QPushButton {{ background: {bg2}; border: 1px solid #333a49; border-radius: 6px; padding: 5px 8px; }}
        QPushButton:hover {{ border-color: {accent}; }}
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit, QPlainTextEdit {{
            background: {bg2}; border: 1px solid #333a49; border-radius: 5px; padding: 3px; color: {fg};
        }}
        QTabWidget::pane {{ border: 1px solid #2c3340; }}
        QTabBar::tab {{ background: {bg2}; padding: 6px 14px; border-radius: 4px 4px 0 0; }}
        QTabBar::tab:selected {{ background: {accent}; color: #fff; }}
        QStatusBar {{ background: {bg2}; color: {fg2}; }}
        QSlider::groove:horizontal {{ height: 6px; background: #2c3340; border-radius: 3px; }}
        QSlider::handle:horizontal {{ width: 14px; background: {accent}; border-radius: 7px; margin: -4px 0; }}
        QLabel {{ color: {fg2}; }}
        QGroupBox {{ border: 1px solid #333a49; border-radius: 6px; margin-top: 8px; padding-top: 8px; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; }}
        """)

    # ── doc management ──
    def current_doc(self):
        i = self.tabs.currentIndex()
        return self.docs[i] if 0 <= i < len(self.docs) else None

    def current_canvas(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, CanvasView) else None

    def _doc_op(self, fn):
        doc = self.current_doc()
        if doc is None:
            return
        fn(doc)
        doc.invalidate()
        doc.changed.emit()

    def _canvas_call(self, name, *args):
        c = self.current_canvas()
        if c is not None:
            getattr(c, name)(*args)

    def _zoom(self, factor):
        c = self.current_canvas()
        if c:
            c.set_zoom(c.zoom * factor)

    def new_document_dialog(self):
        dlg = NewDocDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.new_document(dlg.w.value(), dlg.h.value(),
                              background=dlg.background.currentText())

    def new_document(self, w, h, name=None, background="Transparent"):
        name = name or f"Untitled-{len(self.docs) + 1}"
        doc = Document(w, h, name)
        img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        if background == "White":
            img.fill(QColor(255, 255, 255, 255))
        elif background == "Black":
            img.fill(QColor(0, 0, 0, 255))
        elif background == "Background color":
            img.fill(self.state.bg)
        layer = Layer("Background", w, h, img)
        doc.layers.append(layer)
        doc.active = 0
        doc.snapshot_baseline()
        self.docs.append(doc)
        canvas = CanvasView(doc, self.state)
        canvas.cursor_moved.connect(self._on_cursor_moved)
        canvas.zoom_changed.connect(self._on_zoom_changed)
        canvas.status.connect(lambda s: self.lbl_msg.setText(s))
        self.tabs.addTab(canvas, name)
        self.tabs.setCurrentIndex(len(self.docs) - 1)
        QTimer.singleShot(0, canvas.fit_to_screen)
        self._refresh_layers()
        self._refresh_history()
        self._update_title()

    def close_doc(self, index):
        if 0 <= index < len(self.docs):
            self.docs.pop(index)
            self.tabs.removeTab(index)
        if not self.docs:
            self.new_document(1280, 720)

    def _on_tab_changed(self, _):
        if self.current_doc() is None:
            return
        self._refresh_layers()
        self._refresh_history()
        self._update_title()

    def _update_title(self):
        doc = self.current_doc()
        title = T("app_title")
        if doc:
            title = f"{doc.name}{'*' if doc.history.can_undo() else ''} — {title}"
        self.setWindowTitle(title)

    # ── files ──
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, T("open"), "",
            "Images & Projects (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff *.dpx *.dragonpixel);;All files (*)")
        if path:
            self.open_path(path)

    def open_path(self, path):
        try:
            if path.lower().endswith(DPX_EXT):
                self.load_project(path)
            else:
                self.load_image(path)
            self._add_recent(path)
        except Exception as exc:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to open:\n{exc}")

    def _make_canvas(self, doc):
        canvas = CanvasView(doc, self.state)
        canvas.cursor_moved.connect(self._on_cursor_moved)
        canvas.zoom_changed.connect(self._on_zoom_changed)
        canvas.status.connect(lambda s: self.lbl_msg.setText(s))
        self.tabs.addTab(canvas, doc.name)
        self.tabs.setCurrentIndex(len(self.docs) - 1)
        QTimer.singleShot(0, canvas.fit_to_screen)
        self._refresh_layers()
        self._refresh_history()

    def load_image(self, path):
        img = QImage(path)
        if img.isNull():
            raise ValueError("Unsupported or corrupted image.")
        doc = Document(img.width(), img.height(), os.path.basename(path))
        doc.path = path
        doc.layers.append(Layer("Background", doc.width, doc.height, img))
        doc.active = 0
        doc.snapshot_baseline()
        self.docs.append(doc)
        self._make_canvas(doc)

    def load_project(self, path):
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            for n in names:
                if n.startswith("/") or ".." in n.replace("\\", "/").split("/"):
                    raise ValueError("Unsafe project")
            if "manifest.json" not in names:
                raise ValueError("Missing manifest.json")
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            if manifest.get("format") not in ("dragonpixel", "dpx"):
                raise ValueError("Unknown project format")
            w, h = int(manifest["width"]), int(manifest["height"])
            doc = Document(w, h, manifest.get("name", os.path.basename(path)))
            doc.path = path
            for i, ld in enumerate(manifest.get("layers", [])):
                fname = f"layer_{i}.png"
                if fname not in names:
                    raise ValueError(f"Missing layer: {fname}")
                img = QImage.fromData(zf.read(fname), "PNG")
                if img.isNull():
                    raise ValueError(f"Corrupt layer: {fname}")
                layer = Layer(ld.get("name", f"Layer {i}"), w, h, img,
                              ld.get("kind", "pixel"), ld.get("params") or {})
                layer.visible = bool(ld.get("visible", True))
                layer.opacity = float(ld.get("opacity", 1.0))
                layer.blend = ld.get("blend", "Normal")
                layer.locked = bool(ld.get("locked", False))
                if ld.get("has_mask"):
                    mname = f"mask_{i}.png"
                    if mname in names:
                        mimg = QImage.fromData(zf.read(mname), "PNG")
                        if not mimg.isNull():
                            layer.mask = mimg.convertToFormat(QImage.Format_Grayscale8)
                            layer.mask_enabled = bool(ld.get("mask_enabled", True))
                doc.layers.append(layer)
            if not doc.layers:
                doc.layers.append(Layer("Background", w, h))
            doc.active = min(int(manifest.get("active", 0)), len(doc.layers) - 1)
            doc.snapshot_baseline()
        self.docs.append(doc)
        self._make_canvas(doc)

    def save_file(self):
        doc = self.current_doc()
        if doc is None:
            return
        if not doc.path:
            self.save_file_as()
            return
        try:
            if doc.path.lower().endswith(DPX_EXT):
                self.save_project(doc, doc.path)
            else:
                self.export_to(doc, doc.path)
            self.lbl_msg.setText(f"Saved: {os.path.basename(doc.path)}")
        except Exception as exc:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", str(exc))

    def save_file_as(self):
        doc = self.current_doc()
        if doc is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, T("save_as"), doc.name,
            "Dragon Pixel Project (*.dpx);;PNG (*.png);;JPEG (*.jpg);;WebP (*.webp);;BMP (*.bmp)")
        if not path:
            return
        try:
            if path.lower().endswith(DPX_EXT):
                self.save_project(doc, path)
            else:
                self.export_to(doc, path)
            doc.path = path
            doc.name = os.path.basename(path)
            self.tabs.setTabText(self.tabs.currentIndex(), doc.name)
            doc.snapshot_baseline()
            self._add_recent(path)
            self._update_title()
        except Exception as exc:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", str(exc))

    def save_project(self, doc, path):
        manifest = {"format": "dpx", "version": 1,
                    "width": doc.width, "height": doc.height, "name": doc.name,
                    "active": doc.active, "layers": [],
                    "app": f"Dragon Pixel {APP_VERSION}"}
        tmp = path + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, layer in enumerate(doc.layers):
                buf = QBuffer(); buf.open(QIODevice.WriteOnly)
                layer.image.save(buf, "PNG")
                zf.writestr(f"layer_{i}.png", bytes(buf.data()))
                if layer.mask is not None:
                    mbuf = QBuffer(); mbuf.open(QIODevice.WriteOnly)
                    layer.mask.save(mbuf, "PNG")
                    zf.writestr(f"mask_{i}.png", bytes(mbuf.data()))
                manifest["layers"].append({
                    "name": layer.name, "visible": layer.visible,
                    "opacity": layer.opacity, "blend": layer.blend,
                    "kind": layer.kind, "params": layer.params,
                    "locked": layer.locked, "has_mask": layer.mask is not None,
                    "mask_enabled": layer.mask_enabled,
                })
            zf.writestr("manifest.json",
                        json.dumps(manifest, ensure_ascii=False, indent=1))
        os.replace(tmp, path)
        doc.path = path
        doc.snapshot_baseline()

    def export_file(self):
        doc = self.current_doc()
        if doc is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, T("export"), doc.name + ".png",
            "PNG (*.png);;JPEG (*.jpg);;WebP (*.webp);;BMP (*.bmp);;TIFF (*.tif)")
        if path:
            try:
                self.export_to(doc, path)
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def export_to(self, doc, path):
        comp = doc.composite()
        img = comp.convertToFormat(QImage.Format_ARGB32)
        if not img.save(path):
            raise IOError(f"Cannot save: {path}")

    def export_layers(self):
        doc = self.current_doc()
        if doc is None:
            return
        folder = QFileDialog.getExistingDirectory(self, T("export_layers"))
        if not folder:
            return
        for i, layer in enumerate(doc.layers):
            safe = "".join(c for c in layer.name if c.isalnum() or c in " -_") or f"layer_{i}"
            layer.image.save(os.path.join(folder, f"{i:02d}_{safe}.png"), "PNG")
        QMessageBox.information(self, T("export_layers"),
                                f"Exported {len(doc.layers)} layers.")

    # ── edit / clipboard ──
    def undo(self):
        doc = self.current_doc()
        if doc:
            doc.history.undo()
            self._refresh_layers()
            self._refresh_history()
            self._update_title()

    def redo(self):
        doc = self.current_doc()
        if doc:
            doc.history.redo()
            self._refresh_layers()
            self._refresh_history()
            self._update_title()

    def copy_selection(self):
        doc = self.current_doc()
        if doc is None:
            return
        layer = doc.active_layer()
        if layer is None:
            return
        src = layer.image
        if doc.selection is not None:
            out = QImage(doc.width, doc.height, QImage.Format_ARGB32_Premultiplied)
            out.fill(Qt.transparent)
            p = QPainter(out)
            p.drawImage(0, 0, src)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.drawImage(0, 0, doc.selection.convertToFormat(QImage.Format_Alpha8))
            p.end()
            pix = out
        else:
            pix = src.copy()
        QApplication.clipboard().setImage(pix)
        self.lbl_msg.setText("Copied")

    def cut_selection(self):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer is None:
            return
        self.copy_selection()
        before = layer.image.copy()
        p = QPainter(layer.image)
        if doc.selection is not None:
            p.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            p.drawImage(0, 0, doc.selection.convertToFormat(QImage.Format_Alpha8))
        else:
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            p.fillRect(layer.image.rect(), Qt.transparent)
        p.end()
        doc.commit_pixels("Cut", doc.active, before)
        doc.invalidate()
        doc.changed.emit()

    def paste_selection(self, as_new_layer=False):
        doc = self.current_doc()
        if doc is None:
            return
        img = QApplication.clipboard().image()
        if img.isNull():
            return
        if img.width() > doc.width or img.height() > doc.height:
            img = img.scaled(doc.width, doc.height,
                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if as_new_layer:
            new_layer = Layer("Pasted", doc.width, doc.height, img)
            idx = doc.add_layer(new_layer)
            doc.push_custom("Paste Layer",
                            lambda: doc.remove_layer(idx),
                            lambda: None, new_layer.nbytes())
        else:
            layer = doc.active_layer()
            if layer is None:
                return
            before = layer.image.copy()
            p = QPainter(layer.image)
            p.drawImage(0, 0, img)
            p.end()
            doc.commit_pixels("Paste", doc.active, before)
        doc.invalidate()
        doc.changed.emit()
        self._refresh_layers()

    def _on_history_clicked(self, item):
        doc = self.current_doc()
        if doc is None:
            return
        pos = item.data(Qt.UserRole)
        if pos is not None:
            doc.history.jump_to(pos)
            self._refresh_layers()
            self._refresh_history()

    def _refresh_history(self):
        doc = self.current_doc()
        self.history_list.blockSignals(True)
        self.history_list.clear()
        if doc:
            base = QListWidgetItem("— Original State")
            base.setData(Qt.UserRole, -1)
            self.history_list.addItem(base)
            for i, cmd in enumerate(doc.history.entries):
                it = QListWidgetItem(cmd.label)
                it.setData(Qt.UserRole, i)
                self.history_list.addItem(it)
                if i == doc.history.index:
                    self.history_list.setCurrentItem(it)
        self.history_list.blockSignals(False)

    # ── layers ──
    def _refresh_layers(self):
        doc = self.current_doc()
        self._ui_lock = True
        self.layer_list.clear()
        if doc:
            for i in range(len(doc.layers) - 1, -1, -1):
                layer = doc.layers[i]
                it = QListWidgetItem(layer.name)
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
                it.setCheckState(Qt.Checked if layer.visible else Qt.Unchecked)
                it.setData(Qt.UserRole, i)
                thumb = QPixmap.fromImage(layer.image.scaled(
                    32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                it.setIcon(QIcon(thumb))
                self.layer_list.addItem(it)
                if i == doc.active:
                    self.layer_list.setCurrentItem(it)
            layer = doc.active_layer()
            if layer:
                self.blend_combo.setCurrentText(layer.blend)
                self.opacity_slider.setValue(int(layer.opacity * 100))
        self._ui_lock = False

    def _on_layer_item_changed(self, item):
        if self._ui_lock:
            return
        doc = self.current_doc()
        if doc is None:
            return
        idx = item.data(Qt.UserRole)
        if idx is None or not (0 <= idx < len(doc.layers)):
            return
        layer = doc.layers[idx]
        layer.visible = item.checkState() == Qt.Checked
        if item.text() and item.text() != layer.name:
            layer.name = item.text()
        doc.invalidate()
        doc.changed.emit()
        self._refresh_layers()

    def _on_layer_row_changed(self, _row):
        if self._ui_lock:
            return
        doc = self.current_doc()
        item = self.layer_list.currentItem()
        if doc is None or item is None:
            return
        idx = item.data(Qt.UserRole)
        if idx is not None:
            doc.active = idx
            self._refresh_layers()

    def _on_blend_changed(self, mode):
        if self._ui_lock:
            return
        doc = self.current_doc()
        if doc and doc.active_layer():
            doc.active_layer().blend = mode
            doc.invalidate()
            doc.changed.emit()

    def _on_opacity_changed(self, val):
        if self._ui_lock:
            return
        doc = self.current_doc()
        if doc and doc.active_layer():
            doc.active_layer().opacity = val / 100.0
            doc.invalidate()
            doc.changed.emit()

    def add_layer(self):
        doc = self.current_doc()
        if doc:
            idx = doc.new_layer()
            doc.push_custom("New Layer",
                            lambda: doc.remove_layer(idx),
                            lambda: None)
            self._refresh_layers()

    def duplicate_layer(self):
        doc = self.current_doc()
        if doc and doc.active_layer():
            clone = doc.active_layer().clone()
            idx = doc.add_layer(clone, doc.active + 1)
            doc.push_custom("Duplicate Layer",
                            lambda: doc.remove_layer(idx),
                            lambda: None, clone.nbytes())
            self._refresh_layers()

    def delete_layer(self):
        doc = self.current_doc()
        if doc and len(doc.layers) > 1:
            doc.remove_layer(doc.active)
            self._refresh_layers()

    def add_mask(self):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer and layer.mask is None:
            m = QImage(doc.width, doc.height, QImage.Format_Grayscale8)
            m.fill(255)
            layer.mask = m
            layer.mask_enabled = True
            doc.invalidate()
            doc.changed.emit()

    def remove_mask(self):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer:
            layer.mask = None
            doc.invalidate()
            doc.changed.emit()

    def invert_mask(self):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer and layer.mask is not None:
            layer.mask.invertPixels(QImage.InvertRgb)
            doc.invalidate()
            doc.changed.emit()

    def apply_mask(self):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer and layer.mask is not None:
            before = layer.image.copy()
            p = QPainter(layer.image)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.drawImage(0, 0, layer.mask.convertToFormat(QImage.Format_Alpha8))
            p.end()
            layer.mask = None
            doc.commit_pixels("Apply Mask", doc.active, before)
            doc.invalidate()
            doc.changed.emit()

    def layer_style_dialog(self):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer is None:
            return
        dlg = LayerStyleDialog(self, layer.style)
        if dlg.exec() == QDialog.Accepted:
            layer.style = dlg.result_style()
            doc.invalidate()
            doc.changed.emit()
            self._refresh_layers()

    # ── selection ──
    def select_all(self):
        doc = self.current_doc()
        if doc:
            m = QImage(doc.width, doc.height, QImage.Format_Grayscale8)
            m.fill(255)
            doc.selection = m
            self._canvas_call("update")

    def deselect(self):
        doc = self.current_doc()
        if doc:
            doc.selection = None
            self._canvas_call("update")

    def invert_selection(self):
        doc = self.current_doc()
        if doc:
            if doc.selection is None:
                m = QImage(doc.width, doc.height, QImage.Format_Grayscale8)
                m.fill(255)
                doc.selection = m
            else:
                doc.selection.invertPixels(QImage.InvertRgb)
            self._canvas_call("update")

    def feather_selection(self):
        doc = self.current_doc()
        if doc and doc.selection is not None:
            r, ok = QInputDialog.getInt(self, T("feather"), "Radius (px):", 4, 0, 100)
            if ok and r > 0:
                doc.selection = eng_blur(doc.selection, r)
                self._canvas_call("update")

    def grow_selection(self, sign):
        doc = self.current_doc()
        if doc is None or doc.selection is None:
            return
        n, ok = QInputDialog.getInt(self, T("expand"), "Pixels:", 4, 1, 200)
        if not ok:
            return
        if _use_engine():
            doc.selection = eng_dilate(doc.selection, n) if sign > 0 else eng_erode(doc.selection, n)
        else:
            m = QImage(doc.selection)
            p = QPainter(m)
            off = sign * n
            p.drawImage(off, 0, m); p.drawImage(-off, 0, m)
            p.drawImage(0, off, m); p.drawImage(0, -off, m)
            p.end()
            doc.selection = m
        self._canvas_call("update")

    def crop_to_selection(self):
        doc = self.current_doc()
        if doc is None or doc.selection is None:
            QMessageBox.information(self, T("crop_sel"), "No selection.")
            return
        bm = QBitmap.fromImage(doc.selection.convertToFormat(QImage.Format_Mono))
        region = QRegion(bm)
        if region.isEmpty():
            QMessageBox.information(self, T("crop_sel"), "Empty selection.")
            return
        r = region.boundingRect()
        doc.crop(r.x(), r.y(), r.width(), r.height())
        self._canvas_call("fit_to_screen")

    def remove_background(self):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer is None:
            return
        before = layer.image.copy()
        total = QImage(doc.width, doc.height, QImage.Format_Grayscale8)
        total.fill(0)
        p = QPainter(total)
        for (x, y) in ((0, 0), (doc.width - 1, 0), (0, doc.height - 1),
                       (doc.width - 1, doc.height - 1)):
            m = flood_fill_mask(layer.image, x, y, self.state.tolerance)
            p.drawImage(0, 0, m)
        p.end()
        p = QPainter(layer.image)
        p.setCompositionMode(QPainter.CompositionMode_DestinationOut)
        p.drawImage(0, 0, total)
        p.end()
        doc.commit_pixels("Remove Background", doc.active, before)
        doc.invalidate()
        doc.changed.emit()

    # ── filters ──
    def _run_param_dialog(self, title, specs, fn):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer is None:
            return
        canvas = self.current_canvas()
        original = layer.image.copy()

        def preview(img):
            if canvas:
                canvas.set_preview(img)

        def accept(img):
            layer.image = img
            doc.commit_pixels(title, doc.active, original)
            doc.invalidate()
            doc.changed.emit()
            if canvas:
                canvas.set_preview(None)
            self._refresh_layers()

        dlg = ParamDialog(self, title, specs, fn, preview, accept)
        dlg.exec()

    def adjust_brightness_contrast(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("brightness_contrast"),
            [("brightness", "Brightness", -100, 100, 0, False),
             ("contrast", "Contrast", -100, 100, 0, False),
             ("exposure", "Exposure", -3.0, 3.0, 0.0, True),
             ("gamma", "Gamma", 0.1, 5.0, 1.0, True)],
            lambda v: eng_adjust(orig, brightness=v["brightness"],
                                 contrast=v["contrast"],
                                 exposure=v["exposure"], gamma=v["gamma"]))

    def adjust_hue_saturation(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("hue_sat"),
            [("hue", "Hue", -180, 180, 0, False),
             ("saturation", "Saturation", -100, 100, 0, False)],
            lambda v: eng_adjust(orig, hue=v["hue"], saturation=v["saturation"]))

    def auto_contrast(self):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer is None:
            return
        before = layer.image.copy()
        layer.image = eng_adjust(layer.image, contrast=20)
        doc.commit_pixels("Auto Contrast", doc.active, before)
        doc.invalidate()
        doc.changed.emit()

    def filter_simple(self, label, fn):
        doc = self.current_doc()
        layer = doc.active_layer() if doc else None
        if layer is None:
            return
        before = layer.image.copy()
        layer.image = fn(layer.image)
        doc.commit_pixels(label, doc.active, before)
        doc.invalidate()
        doc.changed.emit()
        self._refresh_layers()

    def dialog_blur(self, kind):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        fn = eng_blur if kind == "gaussian" else eng_box_blur
        self._run_param_dialog(
            T("gaussian_blur") if kind == "gaussian" else T("box_blur"),
            [("radius", "Radius", 1, 200, 4, False)],
            lambda v: fn(orig, v["radius"]))

    def dialog_sharpen(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("sharpen"), [("amount", "Amount", 0.1, 5.0, 1.0, True)],
            lambda v: eng_sharpen(orig, v["amount"]))

    def dialog_posterize(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("posterize"), [("levels", "Levels", 2, 64, 6, False)],
            lambda v: eng_posterize(orig, v["levels"]))

    def dialog_threshold(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("threshold"), [("level", "Level", 0, 255, 128, False)],
            lambda v: eng_threshold(orig, v["level"]))

    def dialog_pixelate(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("pixelate"), [("block", "Block Size", 2, 128, 10, False)],
            lambda v: eng_pixelate(orig, v["block"]))

    def dialog_noise(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("noise"), [("amount", "Amount", 1, 100, 20, False)],
            lambda v: eng_add_noise(orig, v["amount"]))

    def dialog_vignette(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("vignette"), [("strength", "Strength", 0.05, 1.0, 0.5, True)],
            lambda v: eng_vignette(orig, v["strength"]))

    def dialog_motion_blur(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("motion_blur"),
            [("distance", "Distance", 1, 100, 12, False),
             ("angle", "Angle", -180, 180, 0, False)],
            lambda v: eng_motion_blur(orig, v["distance"], v["angle"]))

    def dialog_radial_blur(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("radial_blur"),
            [("amount", "Amount", 0.01, 1.0, 0.1, True),
             ("quality", "Quality", 4, 32, 12, False)],
            lambda v: eng_radial_blur(orig, v["amount"], v["quality"]))

    def dialog_levels(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("levels"),
            [("in_black", "Input Black", 0, 255, 0, False),
             ("in_white", "Input White", 0, 255, 255, False),
             ("gamma", "Gamma", 0.1, 5.0, 1.0, True),
             ("out_black", "Output Black", 0, 255, 0, False),
             ("out_white", "Output White", 0, 255, 255, False)],
            lambda v: eng_levels(orig, v["in_black"], v["in_white"], v["gamma"],
                                 v["out_black"], v["out_white"]))

    def dialog_color_balance(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("color_balance"),
            [("r", "Cyan–Red", -100, 100, 0, False),
             ("g", "Magenta–Green", -100, 100, 0, False),
             ("b", "Yellow–Blue", -100, 100, 0, False)],
            lambda v: eng_color_balance(orig, v["r"], v["g"], v["b"]))

    def dialog_photo_filter(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("photo_filter"),
            [("r", "Red", 0.0, 2.0, 1.0, True),
             ("g", "Green", 0.0, 2.0, 1.0, True),
             ("b", "Blue", 0.0, 2.0, 1.0, True),
             ("density", "Density", 0.0, 1.0, 0.5, True)],
            lambda v: eng_photo_filter(orig, v["r"], v["g"], v["b"], v["density"]))

    def dialog_high_pass(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("high_pass"), [("radius", "Radius", 1, 50, 4, False)],
            lambda v: eng_high_pass(orig, v["radius"]))

    def dialog_median(self):
        layer = self.current_doc().active_layer()
        if layer is None:
            return
        orig = layer.image
        self._run_param_dialog(
            T("median"), [("radius", "Radius", 1, 10, 2, False)],
            lambda v: eng_median(orig, v["radius"]))

    # ── size / view / settings ──
    def image_size_dialog(self):
        doc = self.current_doc()
        if doc is None:
            return
        w, ok = QInputDialog.getInt(self, T("resize_image"), "Width:", doc.width, 1, 20000)
        if not ok:
            return
        h, ok = QInputDialog.getInt(self, T("resize_image"), "Height:", doc.height, 1, 20000)
        if not ok:
            return
        doc.resize_image(w, h)
        self._canvas_call("fit_to_screen")
        self._refresh_layers()

    def canvas_size_dialog(self):
        doc = self.current_doc()
        if doc is None:
            return
        w, ok = QInputDialog.getInt(self, T("resize_canvas"), "Width:", doc.width, 1, 20000)
        if not ok:
            return
        h, ok = QInputDialog.getInt(self, T("resize_canvas"), "Height:", doc.height, 1, 20000)
        if not ok:
            return
        doc.resize_canvas(w, h)
        self._canvas_call("fit_to_screen")
        self._refresh_layers()

    def toggle_rulers(self, v):
        self.state.show_rulers = v
        self._canvas_call("update")

    def toggle_grid(self, v):
        self.state.show_grid = v
        self._canvas_call("update")

    def toggle_split(self, v):
        self.state.split_view = v
        doc = self.current_doc()
        if v and doc and doc.baseline is None:
            doc.snapshot_baseline()
        self._canvas_call("update")

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def show_settings(self):
        dlg = QDialog(self); dlg.setWindowTitle(T("prefs"))
        lay = QFormLayout(dlg)
        theme = QComboBox(); theme.addItems(["dark", "light"])
        theme.setCurrentText(self.settings.value("theme", "dark"))
        lang = QComboBox(); lang.addItems(["ar", "en"])
        lang.setCurrentText(self.settings.value("lang", "ar"))
        weak = QCheckBox(T("weak_device"))
        weak.setChecked(self.settings.value("weak_device", False, type=bool))
        force_py = QCheckBox(T("force_python"))
        force_py.setChecked(self.settings.value("force_python", False, type=bool))
        force_py.setEnabled(ENGINE_OK)
        engine_label = QLabel(
            f"{T('engine_status')}: {'Rust ' + ENGINE_VERSION if ENGINE_OK else 'Python only'}")
        lay.addRow("Theme", theme)
        lay.addRow("Language", lang)
        lay.addRow(engine_label)
        lay.addRow(weak)
        lay.addRow(force_py)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addRow(bb)
        if dlg.exec() == QDialog.Accepted:
            self.settings.setValue("theme", theme.currentText())
            self.settings.setValue("weak_device", weak.isChecked())
            self.settings.setValue("force_python", force_py.isChecked())
            if lang.currentText() != self.settings.value("lang", "ar"):
                self.settings.setValue("lang", lang.currentText())
                QMessageBox.information(self, T("language"), T("restart_lang"))
            self._apply_theme()
            self.lbl_msg.setText("Settings applied. Some changes require reopening tabs.")

    def show_about(self):
        engine = f"Rust {ENGINE_VERSION}" if ENGINE_OK else "Python (fallback)"
        QMessageBox.about(
            self, T("about"),
            f"<h2>Dragon Pixel</h2><p>Version {APP_VERSION}</p>"
            f"<p>Free image editor — no NumPy.</p>"
            f"<p>Engine: <b>{engine}</b></p>"
            f"<p>Weak-device mode: "
            f"{'ON' if self.settings.value('weak_device', False, type=bool) else 'OFF'}</p>")

    def _on_cursor_moved(self, x, y):
        self.lbl_pos.setText(f"{x}, {y}")

    def _on_zoom_changed(self, z):
        self.lbl_zoom.setText(f"{int(z * 100)}%")
        doc = self.current_doc()
        if doc:
            self.lbl_dim.setText(f"{doc.width} × {doc.height} px")
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(z * 100))
        self.zoom_slider.blockSignals(False)

    def _pick_color(self, which):
        cur = self.state.fg if which == "fg" else self.state.bg
        c = QColorDialog.getColor(cur, self, "Choose color",
                                  QColorDialog.ShowAlphaChannel)
        if c.isValid():
            if which == "fg":
                self.state.fg = c
            else:
                self.state.bg = c
            self._update_color_buttons()

    def _update_color_buttons(self):
        self.fg_btn.setStyleSheet(
            f"background:{self.state.fg.name()}; color: white; border:1px solid #333a49;")
        self.bg_btn.setStyleSheet(
            f"background:{self.state.bg.name()}; color: white; border:1px solid #333a49;")

    def _on_brush_change(self):
        self.state.brush_size = self.size_spin.value()
        self.state.brush_hardness = self.hard_spin.value()
        self.state.brush_opacity = self.op_spin.value()
        self.state.brush_flow = self.flow_spin.value()
        self.state.brush_spacing = self.spacing_spin.value()

    def set_tool(self, tid):
        self.state.tool = tid
        for k, a in self.tool_actions.items():
            a.blockSignals(True)
            a.setChecked(k == tid)
            a.blockSignals(False)
        canvas = self.current_canvas()
        if canvas:
            cursor = {"move": Qt.SizeAllCursor, "hand": Qt.OpenHandCursor,
                      "zoom": Qt.CrossCursor, "text": Qt.IBeamCursor,
                      "eyedropper": Qt.CrossCursor}.get(tid, Qt.CrossCursor)
            canvas.setCursor(cursor)
            canvas.update()
        self.lbl_msg.setText(f"Tool: {tid}")

    def keyPressEvent(self, e):
        fw = QApplication.focusWidget()
        if isinstance(fw, (QLineEdit, QTextEdit, QPlainTextEdit,
                           QAbstractSpinBox, QComboBox)):
            super().keyPressEvent(e)
            return
        if e.modifiers() == Qt.NoModifier:
            for tid, en, ar, sc, impl, _g in TOOLS:
                if impl and sc and e.key() == getattr(Qt, f"Key_{sc}", None):
                    self.set_tool(tid)
                    return
            if e.key() == Qt.Key_BracketLeft:
                self.state.brush_size = max(1, self.state.brush_size - 2)
                self.size_spin.setValue(self.state.brush_size)
                return
            if e.key() == Qt.Key_BracketRight:
                self.state.brush_size = min(800, self.state.brush_size + 2)
                self.size_spin.setValue(self.state.brush_size)
                return
            if e.key() == Qt.Key_Comma:
                self.state.brush_size = max(1, self.state.brush_size - 2)
                self.size_spin.setValue(self.state.brush_size)
                return
            if e.key() == Qt.Key_Period:
                self.state.brush_size = min(800, self.state.brush_size + 2)
                self.size_spin.setValue(self.state.brush_size)
                return
        super().keyPressEvent(e)


def main():
    try:
        app = QApplication.instance() or QApplication(sys.argv)
    except Exception as exc:
        print(f"\n✗ فشل إنشاء QApplication: {exc}")
        print("هذا يعني عادةً أن نسخة PySide6 لا تدعم نسختك من Python.")
        print(f"Python الحالي: {sys.version.split()[0]}")
        print("\nالحل:\n  1) استخدم Python 3.12:\n"
              "       py -3.12 -m pip install PySide6\n"
              "       py -3.12 dragon_pixel.py\n"
              "  2) أو استخدم البديل الفوري:\n"
              "       python dragon_lite.py\n")
        sys.exit(1)

    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG)

    # ═══════════════════════════════════════════════════════════════
    #  1. توليد اللوجو وحفظه كملف صورة بجانب ملف السكربت أولاً
    # ═══════════════════════════════════════════════════════════════
    icon = make_app_icon(512)  # إنشاء الأيقونة بحجم كبير
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "dragon_pixel_logo.png")

        # استخراج الصورة من QIcon وحفظها كـ PNG
        icon.pixmap(512, 512).save(logo_path, "PNG")
        print(f"✅ تم إنشاء ملف اللوجو وحفظه في: {logo_path}")
    except Exception as e:
        print(f"⚠️ لم نتمكن من حفظ اللوجو على القرص: {e}")

    # ═══════════════════════════════════════════════════════════════
    #  2. إكمال تشغيل التطبيق وعرض الواجهة
    # ═══════════════════════════════════════════════════════════════
    app.setWindowIcon(icon)

    font = QFont("Segoe UI", 9)
    app.setFont(font)

    try:
        win = MainWindow()
    except Exception as exc:
        traceback.print_exc()
        QMessageBox.critical(None, "Dragon Pixel — Startup Error",
                             f"فشل بدء المحرر:\n{exc}")
        sys.exit(1)

    win.setWindowIcon(icon)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()