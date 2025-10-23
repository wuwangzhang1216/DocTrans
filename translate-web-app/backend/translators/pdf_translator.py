#!/usr/bin/env python3
"""
Advanced PDF Translator with Gemini API
Full-featured implementation with layout detection and dual output
Based on PDFMathTranslate architecture
"""

import io
import re
import sys
import logging
import unicodedata
from pathlib import Path
from typing import Optional, Dict, Tuple
import cv2
import numpy as np
import fitz
from google import genai
from pdfminer.converter import PDFConverter
from pdfminer.layout import LTChar, LTFigure, LTLine, LTPage
from pdfminer.pdffont import PDFUnicodeNotDefined, PDFCIDFont
from pdfminer.pdfinterp import PDFGraphicState, PDFResourceManager, PDFPageInterpreter
from pdfminer.utils import apply_matrix_pt, mult_matrix
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdfinterp import PDFContentParser
from pdfminer.pdftypes import dict_value, list_value, PDFObjRef
from pdfminer.psparser import PSKeyword, keyword_name, PSLiteral
from pdfminer.utils import MATRIX_IDENTITY
from pdfminer.pdfcolor import PREDEFINED_COLORSPACE
from pdfminer.psexceptions import PSEOF
import onnx
import onnxruntime
from tqdm import tqdm
try:
    from huggingface_hub import hf_hub_download
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)
logging.getLogger('google_genai').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)

# ==================== DocLayout ONNX Model ====================

class YoloBox:
    def __init__(self, data):
        self.xyxy = data[:4]
        self.conf = data[-2]
        self.cls = data[-1]

class YoloResult:
    def __init__(self, boxes, names):
        self.boxes = [YoloBox(data=d) for d in boxes]
        self.boxes.sort(key=lambda x: x.conf, reverse=True)
        self.names = names

class DocLayoutModel:
    def __init__(self, model_path: str):
        self.model_path = model_path
        model = onnx.load(model_path)
        metadata = {d.key: d.value for d in model.metadata_props}
        
        import ast
        self._stride = ast.literal_eval(metadata["stride"])
        self._names = ast.literal_eval(metadata["names"])
        self.model = onnxruntime.InferenceSession(model.SerializeToString())

    @staticmethod
    def from_pretrained(model_path: str = None):
        """Load model from local path or download from HuggingFace if not found"""
        if model_path is None:
            model_path = "doclayout_yolo_docstructbench_imgsz1024.onnx"

        # Try to load local model first
        if not Path(model_path).exists():
            if HF_AVAILABLE:
                log.info(f"Model not found locally, downloading from HuggingFace...")
                model_path = hf_hub_download(
                    repo_id="wybxc/DocLayout-YOLO-DocStructBench-onnx",
                    filename="doclayout_yolo_docstructbench_imgsz1024.onnx",
                )
            else:
                raise FileNotFoundError(
                    f"Model file '{model_path}' not found. "
                    f"Install huggingface_hub to auto-download: pip install huggingface_hub"
                )

        return DocLayoutModel(model_path)

    @property
    def stride(self):
        return self._stride

    def resize_and_pad_image(self, image, new_shape):
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)
        h, w = image.shape[:2]
        new_h, new_w = new_shape
        r = min(new_h / h, new_w / w)
        resized_h, resized_w = int(round(h * r)), int(round(w * r))
        image = cv2.resize(image, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)
        
        pad_w = (new_w - resized_w) % self.stride
        pad_h = (new_h - resized_h) % self.stride
        top, bottom = pad_h // 2, pad_h - pad_h // 2
        left, right = pad_w // 2, pad_w - pad_w // 2
        image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        return image

    def scale_boxes(self, img1_shape, boxes, img0_shape):
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])
        pad_x = round((img1_shape[1] - img0_shape[1] * gain) / 2 - 0.1)
        pad_y = round((img1_shape[0] - img0_shape[0] * gain) / 2 - 0.1)
        boxes[..., :4] = (boxes[..., :4] - [pad_x, pad_y, pad_x, pad_y]) / gain
        return boxes

    def predict(self, image, imgsz=1024):
        orig_h, orig_w = image.shape[:2]
        pix = self.resize_and_pad_image(image, new_shape=imgsz)
        pix = np.transpose(pix, (2, 0, 1))
        pix = np.expand_dims(pix, axis=0)
        pix = pix.astype(np.float32) / 255.0
        new_h, new_w = pix.shape[2:]
        
        preds = self.model.run(None, {"images": pix})[0]
        preds = preds[preds[..., 4] > 0.25]
        preds[..., :4] = self.scale_boxes((new_h, new_w), preds[..., :4], (orig_h, orig_w))
        return [YoloResult(boxes=preds, names=self._names)]

# ==================== Gemini Translator ====================

class GeminiTranslator:
    def __init__(self, api_key: str, lang_in: str = "en", lang_out: str = "zh", model: str = "gemini-2.0-flash-lite"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.lang_in = lang_in
        self.lang_out = lang_out
        self.name = "gemini"

    def translate(self, text: str) -> str:
        if not text.strip() or re.match(r"^\{v\d+\}$", text):
            return text
        
        prompt = (
            "You are a professional, authentic machine translation engine. "
            "Only output the translated text, do not include any other text.\n\n"
            f"Translate the following text to {self.lang_out}. "
            "Keep the formula notation {v*} unchanged. "
            "Output translation directly without any additional text.\n\n"
            f"Source Text: {text}\n\n"
            "Translated Text:"
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0}
            )
            return response.text.strip()
        except Exception as e:
            log.error(f"Translation error: {e}")
            return text

# ==================== PDF Converter Extended ====================

class PDFConverterEx(PDFConverter):
    def __init__(self, rsrcmgr: PDFResourceManager) -> None:
        PDFConverter.__init__(self, rsrcmgr, None, "utf-8", 1, None)

    def begin_page(self, page, ctm) -> None:
        (x0, y0, x1, y1) = page.cropbox
        (x0, y0) = apply_matrix_pt(ctm, (x0, y0))
        (x1, y1) = apply_matrix_pt(ctm, (x1, y1))
        mediabox = (0, 0, abs(x0 - x1), abs(y0 - y1))
        self.cur_item = LTPage(page.pageno, mediabox)

    def end_page(self, page):
        return self.receive_layout(self.cur_item)

    def begin_figure(self, name, bbox, matrix) -> None:
        self._stack.append(self.cur_item)
        self.cur_item = LTFigure(name, bbox, mult_matrix(matrix, self.ctm))
        self.cur_item.pageid = self._stack[-1].pageid

    def end_figure(self, _: str) -> None:
        fig = self.cur_item
        self.cur_item = self._stack.pop()
        self.cur_item.add(fig)
        return self.receive_layout(fig)

    def render_char(self, matrix, font, fontsize: float, scaling: float, rise: float,
                    cid: int, ncs, graphicstate: PDFGraphicState) -> float:
        try:
            text = font.to_unichr(cid)
            assert isinstance(text, str), str(type(text))
        except PDFUnicodeNotDefined:
            text = self.handle_undefined_char(font, cid)
        
        textwidth = font.char_width(cid)
        textdisp = font.char_disp(cid)
        item = LTChar(matrix, font, fontsize, scaling, rise, text, textwidth, textdisp, ncs, graphicstate)
        self.cur_item.add(item)
        item.cid = cid
        item.font = font
        return item.adv

class Paragraph:
    def __init__(self, y, x, x0, x1, y0, y1, size, brk):
        self.y = y
        self.x = x
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.size = size
        self.brk = brk

# ==================== Translation Converter ====================

class TranslateConverter(PDFConverterEx):
    def __init__(self, rsrcmgr, translator, layout, noto, noto_name):
        super().__init__(rsrcmgr)
        self.translator = translator
        self.layout = layout
        self.noto = noto
        self.noto_name = noto_name
        self.fontid = {}
        self.fontmap = {}

    def raw_string(self, fcur: str, cstk: str) -> str:
        """Encode text based on font type (CID vs non-CID)"""
        if fcur == self.noto_name:
            return "".join(["%04x" % self.noto.has_glyph(ord(c)) for c in cstk])
        elif fcur in self.fontmap and isinstance(self.fontmap[fcur], PDFCIDFont):
            # CID fonts use 4-digit hex
            return "".join(["%04x" % ord(c) for c in cstk])
        else:
            # Regular fonts use 2-digit hex
            return "".join(["%02x" % ord(c) for c in cstk])

    def vflag(self, font: str, char: str) -> bool:
        if isinstance(font, bytes):
            try:
                font = font.decode('utf-8')
            except UnicodeDecodeError:
                font = ""
        font = font.split("+")[-1]
        
        if re.match(r"\(cid:", char):
            return True
        
        if re.match(r"(CM[^R]|MS.M|XY|MT|BL|RM|EU|LA|RS|LINE|LCIRCLE|TeX-|rsfs|txsy|wasy|stmary|.*Mono|.*Code|.*Ital|.*Sym|.*Math)", font):
            return True
        
        if char and char != " " and (
            unicodedata.category(char[0]) in ["Lm", "Mn", "Sk", "Sm", "Zl", "Zp", "Zs"]
            or ord(char[0]) in range(0x370, 0x400)
        ):
            return True
        
        return False

    def receive_layout(self, ltpage: LTPage):
        sstk = []
        pstk = []
        vbkt = 0
        vstk = []
        vlstk = []
        vfix = 0
        var = []
        varl = []
        varf = []
        vlen = []
        lstk = []
        xt = None
        xt_cls = -1
        vmax = ltpage.width / 4

        # âœ… Diagnostic: count children
        char_count = sum(1 for child in ltpage if isinstance(child, LTChar))
        log.info(f"Page {ltpage.pageid}: Processing {char_count} characters")

        # âœ… First pass: collect all children
        has_text = False
        for child in ltpage:
            if isinstance(child, LTChar):
                has_text = True
                cur_v = False
                layout = self.layout[ltpage.pageid]
                h, w = layout.shape
                cx, cy = np.clip(int(child.x0), 0, w - 1), np.clip(int(child.y0), 0, h - 1)
                cls = layout[cy, cx]

                if child.get_text() == "â€¢":
                    cls = 0

                if (cls == 0 or
                    (cls == xt_cls and len(sstk) > 0 and len(sstk[-1].strip()) > 1 and child.size < pstk[-1].size * 0.79) or
                    self.vflag(child.fontname, child.get_text()) or
                    (child.matrix[0] == 0 and child.matrix[3] == 0)):
                    cur_v = True

                if not cur_v:
                    if vstk and child.get_text() == "(":
                        cur_v = True
                        vbkt += 1
                    if vbkt and child.get_text() == ")":
                        cur_v = True
                        vbkt -= 1

                if (not cur_v or cls != xt_cls or
                    (len(sstk) > 0 and sstk[-1] != "" and abs(child.x0 - xt.x0) > vmax)):
                    if vstk:
                        if (not cur_v and cls == xt_cls and
                            child.x0 > max([vch.x0 for vch in vstk])):
                            vfix = vstk[0].y0 - child.y0
                        if len(sstk) > 0 and sstk[-1] == "":
                            xt_cls = -1
                        if len(sstk) > 0:
                            sstk[-1] += f"{{v{len(var)}}}"
                        vstk_copy = vstk[:]
                        var.append(vstk_copy)
                        varl.append(vlstk[:])
                        varf.append(vfix)
                        vstk = []
                        vlstk = []
                        vfix = 0

                if not vstk:
                    if cls == xt_cls and xt is not None:
                        if child.x0 > xt.x1 + 1:
                            if len(sstk) > 0:
                                sstk[-1] += " "
                        elif child.x1 < xt.x0:
                            if len(sstk) > 0:
                                sstk[-1] += " "
                                pstk[-1].brk = True
                    else:
                        sstk.append("")
                        pstk.append(Paragraph(child.y0, child.x0, child.x0, child.x0, child.y0, child.y1, child.size, False))

                if not cur_v:
                    if len(pstk) > 0 and ((child.size > pstk[-1].size or len(sstk[-1].strip()) == 1) and
                        child.get_text() != " "):
                        pstk[-1].y -= child.size - pstk[-1].size
                        pstk[-1].size = child.size
                    if len(sstk) > 0:
                        sstk[-1] += child.get_text()
                else:
                    if (not vstk and cls == xt_cls and xt is not None and child.x0 > xt.x0):
                        vfix = child.y0 - xt.y0
                    vstk.append(child)

                if len(pstk) > 0:
                    pstk[-1].x0 = min(pstk[-1].x0, child.x0)
                    pstk[-1].x1 = max(pstk[-1].x1, child.x1)
                    pstk[-1].y0 = min(pstk[-1].y0, child.y0)
                    pstk[-1].y1 = max(pstk[-1].y1, child.y1)

                xt = child
                xt_cls = cls

            elif isinstance(child, LTLine):
                layout = self.layout[ltpage.pageid]
                h, w = layout.shape
                cx, cy = np.clip(int(child.x0), 0, w - 1), np.clip(int(child.y0), 0, h - 1)
                cls = layout[cy, cx]
                if vstk and cls == xt_cls:
                    vlstk.append(child)
                else:
                    lstk.append(child)

        # âœ… If no text on page, return empty (graphics will be preserved in ops_base)
        if not has_text or len(sstk) == 0:
            log.warning(f"Page {ltpage.pageid}: No text content (has_text={has_text}, paragraphs={len(sstk)})")
            # Return minimal BT/ET block to preserve page structure (like pdf2zh)
            ops = "BT "
            for l in lstk:
                if l.linewidth < 5:
                    ops += f"ET q 1 0 0 1 {l.pts[0][0]:f} {l.pts[0][1]:f} cm [] 0 d 0 J {l.linewidth:f} w 0 0 m {l.pts[1][0] - l.pts[0][0]:f} {l.pts[1][1] - l.pts[0][1]:f} l S Q BT "
            ops += "ET "
            log.info(f"Page {ltpage.pageid}: Generated minimal ops (no text): {len(ops)} bytes")
            return ops

        log.info(f"Page {ltpage.pageid}: Collected {len(sstk)} paragraphs, {len(var)} formulas")

        if vstk and len(sstk) > 0:
            sstk[-1] += f"{{v{len(var)}}}"
            var.append(vstk)
            varl.append(vlstk)
            varf.append(vfix)
        
        for id, v in enumerate(var):
            l = max([vch.x1 for vch in v]) - v[0].x0
            vlen.append(l)
        
        # Translate paragraphs
        news = []
        for s in tqdm(sstk, desc="Translating"):
            news.append(self.translator.translate(s))
        
        # Generate operations for new document
        ops_list = []
        LANG_LINEHEIGHT_MAP = {
            "zh": 1.4, "zh-cn": 1.4, "zh-tw": 1.4, "ja": 1.1, 
            "ko": 1.2, "en": 1.2, "ar": 1.0, "ru": 0.8
        }
        default_line_height = LANG_LINEHEIGHT_MAP.get(self.translator.lang_out.lower(), 1.1)
        
        for id, new in enumerate(news):
            x = pstk[id].x
            y = pstk[id].y
            x0 = pstk[id].x0
            x1 = pstk[id].x1
            height = pstk[id].y1 - pstk[id].y0
            size = pstk[id].size
            brk = pstk[id].brk
            
            cstk = ""
            fcur = None
            lidx = 0
            tx = x
            ptr = 0

            # Use ops_vals to collect all operations first
            ops_vals = []

            while ptr < len(new):
                vy_regex = re.match(r"\{\s*v([\d\s]+)\}", new[ptr:], re.IGNORECASE)
                mod = 0
                fcur_ = None

                if vy_regex:
                    ptr += len(vy_regex.group(0))
                    try:
                        vid = int(vy_regex.group(1).replace(" ", ""))
                        adv = vlen[vid]
                    except Exception:
                        continue

                    if var[vid][-1].get_text() and unicodedata.category(var[vid][-1].get_text()[0]) in ["Lm", "Mn", "Sk"]:
                        mod = var[vid][-1].width
                else:
                    ch = new[ptr]
                    # Intelligent font selection: try tiro for Latin chars first
                    fcur_ = None
                    try:
                        if "tiro" in self.fontmap and self.fontmap["tiro"].to_unichr(ord(ch)) == ch:
                            fcur_ = "tiro"
                            adv = self.fontmap["tiro"].char_width(ord(ch)) * size  # âœ… Remove * 0.001
                    except Exception:
                        pass

                    if fcur_ is None:
                        fcur_ = self.noto_name
                        adv = self.noto.char_lengths(ch, size)[0]

                    ptr += 1
                
                if (fcur_ != fcur or vy_regex or x + adv > x1 + 0.1 * size):
                    if cstk:
                        ops_vals.append({
                            "type": "text",
                            "font": fcur,
                            "size": size,
                            "x": tx,
                            "dy": 0,
                            "rtxt": self.raw_string(fcur, cstk),
                            "lidx": lidx
                        })
                        cstk = ""
                
                if brk and x + adv > x1 + 0.1 * size:
                    x = x0
                    lidx += 1
                
                if vy_regex:
                    fix = varf[vid] if fcur is not None else 0
                    for vch in var[vid]:
                        vc = chr(vch.cid)
                        vfont_id = self.fontid.get(vch.font, fcur)
                        # âœ… Use raw_string for formulas too
                        ops_vals.append({
                            "type": "text",
                            "font": vfont_id,
                            "size": vch.size,
                            "x": x + vch.x0 - var[vid][0].x0,
                            "dy": fix + vch.y0 - var[vid][0].y0,
                            "rtxt": self.raw_string(vfont_id, vc),
                            "lidx": lidx
                        })

                    for l in varl[vid]:
                        if l.linewidth < 5:
                            ops_vals.append({
                                "type": "line",
                                "x": l.pts[0][0] + x - var[vid][0].x0,
                                "dy": l.pts[0][1] + fix - var[vid][0].y0,
                                "linewidth": l.linewidth,
                                "xlen": l.pts[1][0] - l.pts[0][0],
                                "ylen": l.pts[1][1] - l.pts[0][1],
                                "lidx": lidx
                            })
                else:
                    if not cstk:
                        tx = x
                        if x == x0 and ch == " ":
                            adv = 0
                        else:
                            cstk += ch
                    else:
                        cstk += ch
                
                adv -= mod
                fcur = fcur_
                x += adv
            
            if cstk:
                ops_vals.append({
                    "type": "text",
                    "font": fcur,
                    "size": size,
                    "x": tx,
                    "dy": 0,
                    "rtxt": self.raw_string(fcur, cstk),
                    "lidx": lidx
                })

            # âœ… Adaptive line height AFTER collecting all ops
            line_height = default_line_height
            while (lidx + 1) * size * line_height > height and line_height >= 1:
                line_height -= 0.05

            # Apply line height to all operations
            for vals in ops_vals:
                if vals["type"] == "text":
                    ops_list.append(
                        f"/{vals['font']} {vals['size']:f} Tf 1 0 0 1 {vals['x']:f} "
                        f"{vals['dy'] + y - vals['lidx'] * size * line_height:f} Tm [<{vals['rtxt']}>] TJ "
                    )
                elif vals["type"] == "line":
                    ops_list.append(
                        f"ET q 1 0 0 1 {vals['x']:f} {vals['dy'] - vals['lidx'] * size * line_height:f} cm "
                        f"[] 0 d 0 J {vals['linewidth']:f} w 0 0 m {vals['xlen']:f} {vals['ylen']:f} l S Q BT "
                    )
        
        for l in lstk:
            if l.linewidth < 5:
                ops_list.append(f"ET q 1 0 0 1 {l.pts[0][0]:f} {l.pts[0][1]:f} cm [] 0 d 0 J {l.linewidth:f} w 0 0 m {l.pts[1][0] - l.pts[0][0]:f} {l.pts[1][1] - l.pts[0][1]:f} l S Q BT 0 g ")

        # Set text color to black (0 g for fill, 0 G for stroke) to ensure proper visibility
        ops = f"BT 0 g 0 G {''.join(ops_list)}ET "
        log.info(f"Page {ltpage.pageid}: Generated {len(ops)} bytes of ops_new")
        if len(ops) < 100:
            log.warning(f"Page {ltpage.pageid}: ops_new is very short: {ops[:200]}")
        return ops

# ==================== PDF Interpreter Extended ====================

class PDFPageInterpreterEx(PDFPageInterpreter):
    def __init__(self, rsrcmgr: PDFResourceManager, device: PDFDevice, obj_patch):
        self.rsrcmgr = rsrcmgr
        self.device = device
        self.obj_patch = obj_patch

    # âœ… Path filtering methods to avoid background noise
    def do_S(self):
        """Stroke path - only convert horizontal black lines to LTLine for formulas"""
        # Most table borders will be preserved via ops_base, not converted to LTLine
        self.curpath = []

    def do_s(self):
        """Close and stroke path"""
        self.do_S()

    def do_f(self):
        """Fill path - filter out to avoid background patterns"""
        self.curpath = []

    def do_F(self):
        """Fill path (alternate)"""
        self.curpath = []

    def do_f_a(self):
        """Fill path with even-odd rule"""
        self.curpath = []

    def do_B(self):
        """Fill and stroke path"""
        self.curpath = []

    def do_B_a(self):
        """Fill and stroke path with even-odd rule"""
        self.curpath = []

    def do_b(self):
        """Close, fill and stroke path"""
        self.curpath = []

    def do_b_a(self):
        """Close, fill and stroke path with even-odd rule"""
        self.curpath = []

    def do_n(self):
        """End path without filling or stroking"""
        self.curpath = []

    def init_resources(self, resources: Dict[object, object]) -> None:
        self.resources = resources
        self.fontmap = {}
        self.fontid = {}
        self.xobjmap = {}
        self.csmap = PREDEFINED_COLORSPACE.copy()
        
        if not resources:
            return
        
        for k, v in dict_value(resources).items():
            if k == "Font":
                for fontid, spec in dict_value(v).items():
                    objid = None
                    if isinstance(spec, PDFObjRef):
                        objid = spec.objid
                    spec = dict_value(spec)
                    self.fontmap[fontid] = self.rsrcmgr.get_font(objid, spec)
                    self.fontmap[fontid].descent = 0
                    self.fontid[self.fontmap[fontid]] = fontid
            elif k == "XObject":
                for xobjid, xobjstrm in dict_value(v).items():
                    self.xobjmap[xobjid] = xobjstrm

    def process_page(self, page: PDFPage) -> None:
        (x0, y0, x1, y1) = page.cropbox
        if page.rotate == 90:
            ctm = (0, -1, 1, 0, -y0, x1)
        elif page.rotate == 180:
            ctm = (-1, 0, 0, -1, x1, y1)
        elif page.rotate == 270:
            ctm = (0, 1, -1, 0, y1, -x0)
        else:
            ctm = (1, 0, 0, 1, -x0, -y0)
        
        self.device.begin_page(page, ctm)
        ops_base = self.render_contents(page.resources, page.contents, ctm=ctm)
        self.device.fontid = self.fontid
        self.device.fontmap = self.fontmap
        ops_new = self.device.end_page(page)

        # âœ… Build final content and verify q/Q balance for Adobe compatibility
        final_content = f"q {ops_base}Q 1 0 0 1 {x0} {y0} cm {ops_new}"

        # Check q/Q balance (critical for Adobe Acrobat)
        q_count = final_content.count(' q ') + (1 if final_content.startswith('q ') else 0)
        Q_count = final_content.count(' Q ')

        if q_count != Q_count:
            log.warning(f"Page {page.pageno}: q/Q imbalance detected ({q_count}/{Q_count}), fixing...")
            # Add missing Q operators at the end (before ET if present)
            diff = q_count - Q_count
            if diff > 0:
                # More q than Q, add Q at the end
                if final_content.endswith('ET '):
                    final_content = final_content[:-3] + ('Q ' * diff) + 'ET '
                else:
                    final_content += 'Q ' * diff

        log.info(f"Page {page.pageno}: ops_base={len(ops_base)} bytes, ops_new={len(ops_new)} bytes, final={len(final_content)} bytes, q/Q={q_count}/{Q_count}")
        if not ops_new or len(ops_new) < 10:
            log.warning(f"Page {page.pageno}: ops_new is empty or minimal!")
        if len(ops_base) < 50:
            log.warning(f"Page {page.pageno}: ops_base is minimal: {ops_base[:100]}")

        self.obj_patch[page.page_xref] = final_content
        # âœ… Use list() to ensure proper iteration
        for obj in list(page.contents):
            self.obj_patch[obj.objid] = ""

    def render_contents(self, resources, streams, ctm=MATRIX_IDENTITY):
        self.init_resources(resources)
        self.init_state(ctm)
        return self.execute(list_value(streams))

    def _format_arg(self, arg):
        """Format a PDF argument for content stream"""
        if isinstance(arg, (int, float)):
            return f"{arg:f}"
        elif isinstance(arg, PSLiteral):
            # PSLiteral represents names like /X200, /Pattern, etc.
            # name attribute is bytes, need to decode
            name = arg.name.decode('latin-1') if isinstance(arg.name, bytes) else str(arg.name)
            return f"/{name}"
        else:
            return str(arg)

    def execute(self, streams):
        ops = ""
        try:
            parser = PDFContentParser(streams)
        except PSEOF:
            return ops

        # Path painting operators that we filter (these methods clear self.curpath)
        filtered_painting_ops = {"S", "s", "f", "F", "f*", "B", "B*", "b", "b*", "n"}

        # Path construction operators that should be tracked
        path_construction_ops = {"m", "l", "c", "v", "y", "h", "re"}

        # Graphics state and color space operators that reference external resources
        # Filter these to avoid "cannot find resource" errors
        filtered_resource_ops = {
            "gs",      # Set graphics state (ExtGState) - used for transparency, blend modes
            "cs", "CS",  # Set color space - may reference Pattern or other named color spaces
            "SCN", "scn", "SC", "sc"  # Set color in current color space - may use Pattern
        }

        # Buffer path operations until we know if they will be painted or filtered
        pending_ops = []

        while True:
            try:
                (_, obj) = parser.nextobject()
            except PSEOF:
                break

            if isinstance(obj, PSKeyword):
                name = keyword_name(obj)
                method = "do_%s" % name.replace("*", "_a").replace('"', "_w").replace("'", "_q")

                if hasattr(self, method):
                    func = getattr(self, method)
                    nargs = func.__code__.co_argcount - 1
                    if nargs:
                        args = self.pop(nargs)
                        if len(args) == nargs:
                            params = " ".join([self._format_arg(a) for a in args])
                            func(*args)

                            # Check if this is a filtered painting operator
                            if name in filtered_painting_ops:
                                # Discard pending path operations
                                pending_ops = []
                            elif name in filtered_resource_ops:
                                # Filter resource reference operators to avoid missing resource errors
                                pass
                            elif name[0] == "T" or name in ['"', "'", "EI", "MP", "DP", "BMC", "BDC", "EMC"]:
                                # Text and control operators - don't add to ops
                                pass
                            elif name in path_construction_ops:
                                # Path construction - buffer it in case it needs to be filtered
                                pending_ops.append(f"{params} {name} ")
                            else:
                                # Other operators (colors, transforms, images, etc.)
                                # Flush pending ops first, then add this one
                                ops += "".join(pending_ops)
                                pending_ops = []
                                ops += f"{params} {name} "
                    else:
                        func()

                        # Check if this is a filtered painting operator
                        if name in filtered_painting_ops:
                            # Discard pending path operations
                            pending_ops = []
                        elif name in filtered_resource_ops:
                            # Filter resource reference operators to avoid missing resource errors
                            pass
                        elif name[0] == "T" or name in ['"', "'", "EI", "MP", "DP", "BMC", "BDC", "EMC"]:
                            # Text and control operators - don't add to ops
                            pass
                        elif name in path_construction_ops:
                            # Path construction - buffer it
                            pending_ops.append(f"{name} ")
                        else:
                            # Other operators
                            ops += "".join(pending_ops)
                            pending_ops = []
                            ops += f"{name} "
            else:
                self.push(obj)

        # Flush any remaining non-filtered ops
        ops += "".join(pending_ops)

        return ops

# ==================== Diagnostic Functions ====================

def diagnose_pages(pdf_path: str) -> None:
    """Diagnose PDF page content for debugging"""
    doc = fitz.Document(pdf_path)
    log.info(f"Diagnosing {pdf_path}:")
    for i in range(doc.page_count):
        page = doc[i]
        text = page.get_text()
        images = page.get_images()
        log.info(f"  Page {i}: text={len(text)} chars, images={len(images)}")
        if len(text) < 10:
            log.warning(f"  âš ï¸  Page {i} has very little text!")
    doc.close()

# ==================== Main Translation Function ====================

def translate_pdf(
    input_path: str,
    api_key: str,
    output_dir: Optional[str] = None,
    lang_in: str = "en",
    lang_out: str = "zh",
    model: str = "gemini-2.0-flash-lite",
    font_path: Optional[str] = None,
    model_path: Optional[str] = None
) -> Tuple[str, str]:
    """
    Translate PDF with advanced layout detection and dual output
    
    Returns:
        (mono_output_path, dual_output_path)
    """
    
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"PDF not found: {input_path}")
    
    if output_dir is None:
        output_dir = input_file.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = input_file.stem
    
    log.info("Loading DocLayout model...")
    if model_path is None:
        model_path = "doclayout_yolo_docstructbench_imgsz1024.onnx"
    layout_model = DocLayoutModel.from_pretrained(model_path)
    
    log.info("Initializing translator...")
    translator = GeminiTranslator(api_key, lang_in, lang_out, model)
    
    log.info("Loading fonts...")
    # Use dual font system: tiro for Latin, noto/CJK for target language
    noto_name = "noto"

    # Load CJK/target language font
    if font_path and Path(font_path).exists():
        log.info(f"Using custom font: {font_path}")
        noto = fitz.Font(noto_name, font_path)
        font_list = [("tiro", None), (noto_name, font_path)]
    else:
        log.info("Using built-in CJK font")
        noto_name = "cjk"
        noto = fitz.Font(noto_name)
        font_list = [("tiro", None), (noto_name, None)]
    
    log.info("Processing PDF...")
    
    # Read original PDF
    with open(input_path, 'rb') as f:
        s_raw = f.read()
    
    doc_en = fitz.Document(stream=s_raw)
    stream = io.BytesIO()
    doc_en.save(stream)
    doc_zh = fitz.Document(stream=stream)
    page_count = doc_zh.page_count
    
    # Add fonts to all pages (dual font system)
    # âœ… Insert fonts once and reuse the same font object across all pages
    log.info("Inserting fonts into all pages...")
    font_id = {}
    for page in doc_zh:
        for font_name, font_file in font_list:
            if font_file:
                font_id[font_name] = page.insert_font(font_name, font_file)
            else:
                # For built-in fonts like tiro and cjk
                if font_name == noto_name:
                    font_id[font_name] = page.insert_font(fontname=font_name, fontbuffer=noto.buffer)
                else:
                    font_id[font_name] = page.insert_font(font_name)

    log.info(f"Inserted fonts: {font_id}")
    
    # Insert fonts into resources
    xreflen = doc_zh.xref_length()
    for xref in range(1, xreflen):
        for label in ["Resources/", ""]:
            try:
                font_res = doc_zh.xref_get_key(xref, f"{label}Font")
                target_key_prefix = f"{label}Font/"
                
                if font_res[0] == "xref":
                    resource_xref_id = re.search(r"(\d+) 0 R", font_res[1]).group(1)
                    xref = int(resource_xref_id)
                    font_res = ("dict", doc_zh.xref_object(xref))
                    target_key_prefix = ""
                
                if font_res[0] == "dict":
                    # Inject all fonts (tiro + noto/cjk)
                    for font_name, _ in font_list:
                        target_key = f"{target_key_prefix}{font_name}"
                        font_exist = doc_zh.xref_get_key(xref, target_key)
                        if font_exist[0] == "null":
                            doc_zh.xref_set_key(xref, target_key, f"{font_id[font_name]} 0 R")
            except Exception:
                pass
    
    # Translate pages
    fp = io.BytesIO()
    doc_zh.save(fp)
    
    rsrcmgr = PDFResourceManager()
    layout = {}
    device = TranslateConverter(rsrcmgr, translator, layout, noto, noto_name)
    obj_patch = {}
    interpreter = PDFPageInterpreterEx(rsrcmgr, device, obj_patch)
    
    parser = PDFParser(fp)
    doc = PDFDocument(parser)
    
    log.info(f"Translating {page_count} pages...")
    
    for pageno, page in enumerate(tqdm(list(PDFPage.create_pages(doc)), desc="Pages")):
        page.pageno = pageno
        
        # Get page layout using ONNX model
        pix = doc_zh[page.pageno].get_pixmap()
        image = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)[:, :, ::-1]
        page_layout = layout_model.predict(image, imgsz=int(pix.height / 32) * 32)[0]
        
        # Create layout mask
        box = np.ones((pix.height, pix.width))
        h, w = box.shape
        vcls = ["abandon", "figure", "table", "isolate_formula", "formula_caption"]
        
        for i, d in enumerate(page_layout.boxes):
            if page_layout.names[int(d.cls)] not in vcls:
                x0, y0, x1, y1 = d.xyxy.squeeze()
                x0, y0, x1, y1 = (
                    np.clip(int(x0 - 1), 0, w - 1),
                    np.clip(int(h - y1 - 1), 0, h - 1),
                    np.clip(int(x1 + 1), 0, w - 1),
                    np.clip(int(h - y0 + 1), 0, h - 1),
                )
                box[y0:y1, x0:x1] = i + 2
        
        for i, d in enumerate(page_layout.boxes):
            if page_layout.names[int(d.cls)] in vcls:
                x0, y0, x1, y1 = d.xyxy.squeeze()
                x0, y0, x1, y1 = (
                    np.clip(int(x0 - 1), 0, w - 1),
                    np.clip(int(h - y1 - 1), 0, h - 1),
                    np.clip(int(x1 + 1), 0, w - 1),
                    np.clip(int(h - y0 + 1), 0, h - 1),
                )
                box[y0:y1, x0:x1] = 0
        
        layout[page.pageno] = box
        
        page.page_xref = doc_zh.get_new_xref()
        doc_zh.update_object(page.page_xref, "<<>>")
        doc_zh.update_stream(page.page_xref, b"")
        doc_zh[page.pageno].set_contents(page.page_xref)

        interpreter.process_page(page)

        # âœ… Diagnostic logging
        if page.page_xref in obj_patch:
            ops_content = obj_patch[page.page_xref]
            log.info(f"Page {pageno}: content length = {len(ops_content)} bytes")
            if len(ops_content) < 100:
                log.warning(f"Page {pageno} has minimal content: {ops_content[:200]}")
            # Check ops_base vs ops_new balance
            if "BT" in ops_content and "ET" in ops_content:
                bt_count = ops_content.count("BT")
                et_count = ops_content.count("ET")
                log.info(f"Page {pageno}: BT/ET blocks = {bt_count}/{et_count}")
            else:
                log.warning(f"Page {pageno}: Missing text operators!")
    
    device.close()
    
    # Apply patches
    log.info(f"Applying {len(obj_patch)} patches...")
    for obj_id, ops_new in obj_patch.items():
        doc_zh.update_stream(obj_id, ops_new.encode())
    
    # Create dual output
    doc_en.insert_file(doc_zh)
    for id in range(page_count):
        doc_en.move_page(page_count + id, id * 2 + 1)
    
    # Save outputs
    mono_path = output_dir / f"{filename}-mono.pdf"
    dual_path = output_dir / f"{filename}-dual.pdf"

    log.info("Saving translated PDFs...")
    # Use same parameters as pdf2zh for Adobe compatibility
    # subset_fonts: reduce file size and improve compatibility (requires fontTools)
    try:
        doc_zh.subset_fonts(fallback=True)
        doc_en.subset_fonts(fallback=True)
        log.info("Font subsetting successful")
    except Exception as e:
        if "fontTools" in str(e) or "fonttools" in str(e):
            log.warning("Font subsetting skipped: fontTools not installed (optional dependency)")
            log.info("To enable font subsetting, install: pip install fonttools")
        else:
            log.warning(f"Font subsetting skipped: {e}")

    # Save with compression and cleanup
    # Note: use_objstms requires specific PyMuPDF build, so we omit it for compatibility
    doc_zh.save(str(mono_path), deflate=True, garbage=3)
    doc_en.save(str(dual_path), deflate=True, garbage=3)

    doc_zh.close()
    doc_en.close()

    # âœ… Diagnostic output
    log.info("Running diagnostics on output files...")
    diagnose_pages(str(mono_path))
    diagnose_pages(str(dual_path))

    return str(mono_path), str(dual_path)

# ==================== CLI ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced PDF Translator with Gemini")
    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-k", "--api-key", help="Gemini API key (or set GEMINI_API_KEY)")
    parser.add_argument("-li", "--lang-in", default="en", help="Source language (default: en)")
    parser.add_argument("-lo", "--lang-out", default="zh", help="Target language (default: zh)")
    parser.add_argument("-m", "--model", default="gemini-2.0-flash-lite", help="Gemini model")
    
    args = parser.parse_args()
    
    api_key = args.api_key
    if not api_key:
        import os
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("Error: Gemini API key required via -k or GEMINI_API_KEY env var")
        sys.exit(1)
    
    try:
        mono, dual = translate_pdf(
            args.input,
            api_key,
            args.output,
            args.lang_in,
            args.lang_out,
            args.model
        )
        
        print(f"\nTranslation complete!")
        print(f"  Mono: {mono}")
        print(f"  Dual: {dual}")
    except Exception as e:
        log.exception("Translation failed")
        sys.exit(1)

if __name__ == "__main__":
    # Direct function call with input parameters
    import os

    # Get API key from environment variable
    api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAa-_DIcxorLidlbDZNF72FXLCEaN3lWsg")

    if not api_key:
        print("Error: Set GEMINI_API_KEY environment variable")
        sys.exit(1)

    # Input parameters
    input_pdf = "test.pdf"  # Change this to your PDF path
    output_directory = None  # None uses same directory as input
    source_lang = "en"
    target_lang = "zh"
    gemini_model = "gemini-2.0-flash-lite"

    # Optional: Specify custom font file path (e.g., "GoNotoKurrent-Regular.ttf")
    # Set to None to use built-in CJK font
    custom_font_path = None

    # Optional: Specify ONNX model path (defaults to "doclayout_yolo_docstructbench_imgsz1024.onnx")
    onnx_model_path = "doclayout_yolo_docstructbench_imgsz1024.onnx"

    try:
        mono, dual = translate_pdf(
            input_path=input_pdf,
            api_key=api_key,
            output_dir=output_directory,
            lang_in=source_lang,
            lang_out=target_lang,
            model=gemini_model,
            font_path=custom_font_path,
            model_path=onnx_model_path
        )

        print(f"\nTranslation complete!")
        print(f"  Mono: {mono}")
        print(f"  Dual: {dual}")
    except Exception as e:
        log.exception("Translation failed")
        sys.exit(1)
# ==================== Module Wrapper ====================

class PDFTranslator:
    """Wrapper class for modular architecture"""

    def __init__(self, translation_client):
        self.client = translation_client

    def translate(self, input_path: str, output_path: str, target_language: str,
                 model_path: Optional[str] = None, font_path: Optional[str] = None) -> Tuple[str, str]:
        import os
        # Use API key from the translation client
        api_key = self.client.api_key if hasattr(self.client, 'api_key') and self.client.api_key else os.environ.get('GEMINI_API_KEY')
        output_dir = Path(output_path).parent if output_path else None

        return translate_pdf(
            input_path=input_path,
            api_key=api_key,
            output_dir=str(output_dir) if output_dir else None,
            lang_in="en",
            lang_out=target_language,
            model=self.client.model if hasattr(self.client, 'model') else "gemini-2.0-flash-lite",
            font_path=font_path,
            model_path=model_path
        )

    def translate_with_overlay(self, input_path: str, output_path: str, target_language: str, progress_callback=None):
        """Returns tuple of (mono_path, dual_path) on success"""
        try:
            if progress_callback:
                progress_callback(0.05)
            mono, dual = self.translate(input_path, output_path, target_language)
            if progress_callback:
                progress_callback(1.0)
            print(f"[SUCCESS] Translated PDF saved to: {mono}")
            return (mono, dual)
        except Exception as e:
            print(f"Error: {e}")
            return False

    def translate_with_redaction(self, input_path: str, output_path: str, target_language: str, progress_callback=None):
        return self.translate_with_overlay(input_path, output_path, target_language, progress_callback)

    def translate_hybrid(self, input_path: str, output_path: str, target_language: str, progress_callback=None):
        return self.translate_with_overlay(input_path, output_path, target_language, progress_callback)
