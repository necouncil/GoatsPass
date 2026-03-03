# ── Auto-dependency installer ────────────────────────────────────────────────
import sys, subprocess, importlib

_REQUIRED = [
    ("cryptography",  "cryptography"),
    ("argon2",        "argon2-cffi"),
    ("PIL",           "Pillow"),
]

def _ensure_deps():
    missing = []
    for mod, pkg in _REQUIRED:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    if not missing:
        return
    print(f"[GoatsPass] Installing missing packages: {', '.join(missing)}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        # Try with --break-system-packages (Arch/Manjaro/newer Debian)
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet",
                 "--break-system-packages"] + missing,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            import tkinter as _tk
            import tkinter.messagebox as _mb
            _r = _tk.Tk(); _r.withdraw()
            _mb.showerror(
                "GoatsPass — Missing dependencies",
                f"Failed to auto-install:\n  {chr(10).join(missing)}\n\n"
                f"Please run manually:\n"
                f"  pip install {' '.join(missing)}"
            )
            _r.destroy()
            sys.exit(1)
    # Reload after install
    import importlib as _il
    for mod, _ in _REQUIRED:
        try:
            _il.import_module(mod)
        except Exception:
            pass

_ensure_deps()
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import messagebox
import json, os, secrets, string, time
import platform, hmac, hashlib, struct, base64, webbrowser
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes as _hashes

try:
    from argon2.low_level import hash_secret_raw as _a2_hash, Type as _A2Type
    _HAS_ARGON2 = True
except ImportError:
    _HAS_ARGON2 = False

A_TIME, A_MEM, A_PAR, A_LEN = 4, 131072, 4, 32
SALT_SZ, NONCE_SZ, DB_VER   = 32, 12, 1
LOCK_S   = 300
CLIP_S   = 30
MAX_FAIL = 5
APP_VER  = "1.0"
GITHUB   = "https://github.com/necouncil"
IS_WIN   = platform.system() == "Windows"
_FF      = "Segoe UI" if IS_WIN else "DejaVu Sans"
_FM      = "Consolas" if IS_WIN else "DejaVu Sans Mono"

THEME = {
    "base":     "#09090b",
    "surface":  "#0e0f11",
    "elevated": "#14161a",
    "panel":    "#1a1d23",
    "panel2":   "#1f2229",
    "border":   "#25282f",
    "border2":  "#2e3340",
    "blue":     "#3b82f6",
    "blue_h":   "#60a5fa",
    "blue_dim": "#1e3a5f",
    "green":    "#22c55e",
    "red":      "#ef4444",
    "amber":    "#f59e0b",
    "sky":      "#38bdf8",
    "text":     "#e2e8f0",
    "text2":    "#94a3b8",
    "text3":    "#4b5563",
    "text4":    "#2d3748",
    "sel":      "#1e3a5f",
    "sel_fg":   "#e2e8f0",
    "topbar":   "#0e0f11",
    "sidebar":  "#0e0f11",
}

def _P(key):
    return THEME.get(key, "#000000")

def F(size=11, bold=False, mono=False):
    return (_FM if mono else _FF, size, "bold" if bold else "normal")

def _data_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home())) if IS_WIN \
           else Path.home() / ".local" / "share"
    d = base / "GoatsPass"
    d.mkdir(parents=True, exist_ok=True)
    return d

def load_config() -> dict:
    p = _data_dir() / "config.json"
    try:
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return {}

def save_config(cfg: dict):
    try:
        (_data_dir() / "config.json").write_text(json.dumps(cfg))
    except Exception:
        pass

def _kdf(pwd: str, salt: bytes) -> bytes:
    if _HAS_ARGON2:
        return _a2_hash(
            secret=pwd.encode("utf-8"), salt=salt,
            time_cost=A_TIME, memory_cost=A_MEM,
            parallelism=A_PAR, hash_len=A_LEN,
            type=_A2Type.ID)
    kdf = PBKDF2HMAC(algorithm=_hashes.SHA256(), length=A_LEN,
                     salt=salt, iterations=600_000)
    return kdf.derive(pwd.encode("utf-8"))

def _enc(data: bytes, key: bytes) -> bytes:
    n = secrets.token_bytes(NONCE_SZ)
    return n + AESGCM(key).encrypt(n, data, None)

def _dec(data: bytes, key: bytes) -> bytes:
    return AESGCM(key).decrypt(data[:NONCE_SZ], data[NONCE_SZ:], None)

_SYMS = "!@#$%^&*-_=+?<>"

def make_password(length=20, upper=True, lower=True,
                  digits=True, symbols=True) -> str:
    pool, must = "", []
    if upper:   pool += string.ascii_uppercase;  must.append(secrets.choice(string.ascii_uppercase))
    if lower:   pool += string.ascii_lowercase;  must.append(secrets.choice(string.ascii_lowercase))
    if digits:  pool += string.digits;           must.append(secrets.choice(string.digits))
    if symbols: pool += _SYMS;                   must.append(secrets.choice(_SYMS))
    if not pool: pool = string.ascii_letters + string.digits
    fill = [secrets.choice(pool) for _ in range(max(0, length - len(must)))]
    result = must + fill
    secrets.SystemRandom().shuffle(result)
    return "".join(result)

def make_passphrase(words=4) -> str:
    wl = ["apple","brave","cloud","dream","eagle","flame","grace","house",
          "ivory","jewel","kings","light","magic","night","ocean","pearl",
          "queen","river","storm","tiger","ultra","valor","winds","xenon",
          "amber","bison","cedar","delta","ember","frost","giant","honor",
          "irony","joker","karma","lemon","maple","noble","oasis","piano",
          "quake","radar","solar","tower","umbra","viper","waltz","pixel",
          "alpha","blade","crane","drift","elite","field","globe","helix"]
    chosen = [secrets.choice(wl) for _ in range(words)]
    return "-".join(chosen) + str(secrets.randbelow(9999)).zfill(4)

def pw_strength(pw: str):
    if not pw: return 0, "", _P("text4")
    s = 0
    s += min(30, len(pw) * 2)
    if any(c.isupper() for c in pw): s += 15
    if any(c.islower() for c in pw): s += 10
    if any(c.isdigit() for c in pw): s += 15
    if any(c in _SYMS for c in pw):  s += 20
    if len(set(pw)) >= len(pw) * 0.7: s += 10
    s = min(s, 100)
    if s < 30: return s, "Очень слабый",  _P("red")
    if s < 50: return s, "Слабый",        _P("amber")
    if s < 70: return s, "Средний",       _P("amber")
    if s < 88: return s, "Сильный",       _P("green")
    return      s, "Максимальный",        _P("blue")

def entropy_bits(pw: str) -> float:
    if not pw: return 0.0
    pool = 0
    if any(c.isupper() for c in pw): pool += 26
    if any(c.islower() for c in pw): pool += 26
    if any(c.isdigit() for c in pw): pool += 10
    if any(c in _SYMS for c in pw):  pool += len(_SYMS)
    if pool == 0: pool = 26
    import math
    return round(len(pw) * math.log2(pool), 1)


class Vault:
    def __init__(self):
        self.path     = _data_dir() / "vault.gp"
        self.key      = None
        self.salt     = None
        self.entries  = []
        self._at      = 0.0
        self._locked  = True
        self.fails    = 0
        self._pw_hash = b""

    def exists(self):  return self.path.exists()
    def locked(self):  return self._locked
    def touch(self):   self._at = time.time()
    def idle(self):    return not self._locked and (time.time() - self._at) > LOCK_S

    def create(self, master: str):
        self.salt     = secrets.token_bytes(SALT_SZ)
        self.key      = _kdf(master, self.salt)
        self._pw_hash = hashlib.sha256(master.encode()).digest()
        self.entries  = []
        self._locked  = False
        self.touch(); self._write()

    def unlock(self, master: str) -> bool:
        if self.fails >= MAX_FAIL: return False
        try:
            raw   = self.path.read_bytes()
            salt  = raw[1:SALT_SZ + 1]
            key   = _kdf(master, salt)
            plain = _dec(raw[SALT_SZ + 1:], key)
            data  = json.loads(plain.decode("utf-8"))
            self.salt     = salt
            self.key      = key
            self._pw_hash = hashlib.sha256(master.encode()).digest()
            self.entries  = data.get("entries", [])
            self._locked  = False
            self.fails    = 0
            self.touch(); return True
        except Exception:
            self.fails += 1; return False

    def verify_master(self, master: str) -> bool:
        if self._pw_hash:
            return hmac.compare_digest(
                hashlib.sha256(master.encode()).digest(), self._pw_hash)
        try:
            raw  = self.path.read_bytes()
            salt = raw[1:SALT_SZ + 1]
            key  = _kdf(master, salt)
            _dec(raw[SALT_SZ + 1:], key)
            return True
        except Exception:
            return False

    def change_master(self, old_pw: str, new_pw: str) -> bool:
        if not self.verify_master(old_pw): return False
        self.salt     = secrets.token_bytes(SALT_SZ)
        self.key      = _kdf(new_pw, self.salt)
        self._pw_hash = hashlib.sha256(new_pw.encode()).digest()
        self._write(); return True

    def lock(self):
        self.key = None; self.entries = []
        self._locked = True; self._pw_hash = b""

    def _write(self):
        blob = json.dumps({"v": DB_VER, "entries": self.entries},
                          ensure_ascii=False).encode("utf-8")
        self.path.write_bytes(bytes([DB_VER]) + self.salt + _enc(blob, self.key))

    def save(self):
        if not self._locked: self._write(); self.touch()

    def add(self, **kw) -> dict:
        now = datetime.now().isoformat()
        e = {"id": secrets.token_hex(12),
             "title":    kw.get("title",""),
             "username": kw.get("username",""),
             "password": kw.get("password",""),
             "url":      kw.get("url",""),
             "notes":    kw.get("notes",""),
             "category": kw.get("category","Общее"),
             "tags":     kw.get("tags",[]),
             "totp":     kw.get("totp",""),
             "favorite": False,
             "created":  now, "modified": now, "history": []}
        self.entries.append(e); self.save(); return e

    def update(self, eid: str, **kw):
        for e in self.entries:
            if e["id"] == eid:
                if "password" in kw and kw["password"] != e["password"]:
                    e.setdefault("history",[]).append(
                        {"pw": e["password"], "when": datetime.now().isoformat()})
                    e["history"] = e["history"][-10:]
                e.update(kw); e["modified"] = datetime.now().isoformat(); break
        self.save()

    def delete(self, eid: str):
        self.entries = [e for e in self.entries if e["id"] != eid]
        self.save()

    def toggle_fav(self, eid: str):
        for e in self.entries:
            if e["id"] == eid:
                e["favorite"] = not e.get("favorite", False); break
        self.save()

    def search(self, q: str) -> list:
        if not q: return list(self.entries)
        q = q.lower()
        return [e for e in self.entries
                if q in e.get("title","").lower()
                or q in e.get("username","").lower()
                or q in e.get("url","").lower()
                or q in e.get("category","").lower()
                or any(q in t.lower() for t in e.get("tags",[]))]

    def stats(self) -> dict:
        pws   = [e["password"] for e in self.entries if e.get("password")]
        dupes = len(pws) - len(set(pws))
        weak  = sum(1 for p in pws if pw_strength(p)[0] < 50)
        old   = sum(1 for e in self.entries
                    if e.get("modified") and
                    (datetime.now() - datetime.fromisoformat(e["modified"])).days > 90)
        return {"total": len(self.entries),
                "fav":   sum(1 for e in self.entries if e.get("favorite")),
                "dupes": dupes, "weak": weak, "old": old}

    def get_categories(self) -> list:
        cats = sorted(set(e.get("category","Общее") for e in self.entries))
        return cats if cats else ["Общее"]


def _totp(secret: str):
    pad  = (8 - len(secret) % 8) % 8
    kb   = base64.b32decode(secret.upper().replace(" ","") + "=" * pad)
    t    = int(time.time()) // 30
    msg  = struct.pack(">Q", t)
    h    = hmac.new(kb, msg, hashlib.sha1).digest()
    off  = h[-1] & 0x0F
    code = (struct.unpack(">I", h[off:off+4])[0] & 0x7FFFFFFF) % 1_000_000
    rem  = 30 - int(time.time()) % 30
    return f"{code:06d}", rem


class _Entry(tk.Entry):
    def __init__(self, parent, placeholder="", show_char="", width=0, **kw):
        self._ph    = placeholder
        self._show  = show_char
        self._ph_on = False
        opts = dict(bg=_P("panel"), fg=_P("text"),
                    insertbackground=_P("text"),
                    relief="flat", bd=0, font=F(11),
                    highlightthickness=1,
                    highlightbackground=_P("border2"),
                    highlightcolor=_P("blue"),
                    show=show_char)
        if width: opts["width"] = width
        opts.update(kw)
        super().__init__(parent, **opts)
        if placeholder:
            self._draw_ph()
            self.bind("<FocusIn>",  self._on_fi)
            self.bind("<FocusOut>", self._on_fo)

    def _draw_ph(self):
        self.delete(0, tk.END); self.insert(0, self._ph)
        self.config(fg=_P("text4"), show=""); self._ph_on = True

    def _on_fi(self, _):
        if self._ph_on:
            self.delete(0, tk.END)
            self.config(fg=_P("text"), show=self._show); self._ph_on = False

    def _on_fo(self, _):
        if not self.get(): self._draw_ph()

    def value(self) -> str:
        return "" if self._ph_on else self.get()

    def set_value(self, v: str):
        self._ph_on = False; self.delete(0, tk.END)
        self.config(fg=_P("text"), show=self._show); self.insert(0, v)


class _Btn(tk.Label):
    def __init__(self, parent, text, command,
                 bg=None, fg=None, hover=None,
                 px=16, py=8, font_size=10, bold=False, **kw):
        self._bg  = bg    or _P("panel")
        self._fg  = fg    or _P("text2")
        self._hov = hover or _P("border2")
        super().__init__(parent, text=text,
                         bg=self._bg, fg=self._fg,
                         font=F(font_size, bold),
                         padx=px, pady=py, cursor="hand2", **kw)
        self.bind("<Enter>",    lambda _: self.config(bg=self._hov))
        self.bind("<Leave>",    lambda _: self.config(bg=self._bg))
        self.bind("<Button-1>", lambda _: command())


class _PrimaryBtn(_Btn):
    def __init__(self, parent, text, command, py=9, **kw):
        super().__init__(parent, text=text, command=command,
                         bg=_P("blue"), fg="white", hover=_P("blue_h"),
                         font_size=10, bold=True, py=py, **kw)


class _StrengthBar(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, height=4,
                         bg=_P("border"), highlightthickness=0, **kw)

    def update(self, pw: str):
        sc, lbl, col = pw_strength(pw)
        self.delete("all")
        w = self.winfo_width() or 300
        filled = int(w * min(sc, 100) / 100)
        if filled > 0:
            self.create_rectangle(0, 0, filled, 4, fill=col, outline="")
        return sc, lbl, col


class _GoatLogo(tk.Canvas):
    _img_cache = {}

    def __init__(self, parent, size=56, **kw):
        bg = kw.pop("bg", _P("base"))
        super().__init__(parent, width=size, height=size,
                         bg=bg, highlightthickness=0, **kw)
        self._s  = size
        self._bg = bg
        self._draw()

    def _draw(self):
        s = self._s; self.delete("all")
        icon_path = Path(__file__).parent / "icon.png"
        loaded = False
        if icon_path.exists():
            try:
                from PIL import Image, ImageTk
                key = (str(icon_path), s)
                if key not in _GoatLogo._img_cache:
                    img = Image.open(icon_path).resize((s, s), Image.LANCZOS)
                    _GoatLogo._img_cache[key] = ImageTk.PhotoImage(img)
                self._photo = _GoatLogo._img_cache[key]
                self.create_image(s//2, s//2, image=self._photo, anchor="center")
                loaded = True
            except ImportError:
                try:
                    key = (str(icon_path), s)
                    if key not in _GoatLogo._img_cache:
                        _GoatLogo._img_cache[key] = tk.PhotoImage(file=str(icon_path))
                    self._photo = _GoatLogo._img_cache[key]
                    self.create_image(s//2, s//2, image=self._photo, anchor="center")
                    loaded = True
                except Exception:
                    pass
            except Exception:
                pass
        if not loaded:
            c = _P("blue")
            self.create_oval(2, 2, s-2, s-2, fill=_P("blue_dim"), outline=c, width=1.5)
            self.create_oval(s*.20, s*.46, s*.80, s*.88, fill=c, outline="")
            self.create_oval(s*.30, s*.12, s*.70, s*.52, fill=c, outline="")
            self.create_polygon(s*.32,s*.18, s*.16,s*.04, s*.26,s*.08, fill=c, outline="")
            self.create_polygon(s*.68,s*.18, s*.84,s*.04, s*.74,s*.08, fill=c, outline="")
            self.create_oval(s*.43, s*.44, s*.57, s*.60, fill=c, outline="")
            for ex in [0.40, 0.56]:
                self.create_oval(s*ex, s*.22, s*(ex+.10), s*.32, fill="white", outline="")
                self.create_oval(s*(ex+.02), s*.24, s*(ex+.08), s*.30, fill="#1a1a2e", outline="")
            for lx in [0.24, 0.38, 0.54, 0.68]:
                self.create_rectangle(s*lx, s*.82, s*(lx+.09), s*.96, fill=c, outline="")


class _FAB(tk.Canvas):
    def __init__(self, parent, command, size=52):
        super().__init__(parent, width=size, height=size,
                         bg=_P("base"), highlightthickness=0, cursor="hand2")
        self._s = size; self._cmd = command
        self._render(_P("blue"))
        self.bind("<Enter>",    lambda _: self._render(_P("blue_h")))
        self.bind("<Leave>",    lambda _: self._render(_P("blue")))
        self.bind("<Button-1>", lambda _: command())

    def _render(self, color):
        s = self._s; self.delete("all")
        self.create_oval(2, 2, s-2, s-2, fill=_P("border"), outline="")
        self.create_oval(2, 2, s-2, s-2, fill=color, outline="")
        m, arm = s//2, 11
        self.create_line(m, m-arm, m, m+arm, fill="white", width=2.5, capstyle="round")
        self.create_line(m-arm, m, m+arm, m, fill="white", width=2.5, capstyle="round")


def _divider(parent, padx=0, pady=0):
    f = tk.Frame(parent, bg=_P("border"), height=1)
    if padx: f.pack(fill="x", padx=padx, pady=pady)
    else:    f.pack(fill="x", pady=pady)
    return f


def _tooltip(widget, text: str):
    tip = None
    def _show(e):
        nonlocal tip
        tip = tk.Toplevel(widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{e.x_root+16}+{e.y_root+16}")
        tk.Label(tip, text=text,
                 bg=_P("elevated"), fg=_P("text2"),
                 font=F(9), padx=8, pady=4, relief="flat").pack()
    def _hide(_):
        nonlocal tip
        if tip: tip.destroy(); tip = None
    widget.bind("<Enter>", _show, add="+")
    widget.bind("<Leave>", _hide, add="+")


class _ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=None, **kw):
        bg = bg or _P("elevated")
        super().__init__(parent, bg=bg, **kw)
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._sb = tk.Scrollbar(self, orient="vertical",
                                command=self._canvas.yview,
                                width=6, bg=_P("surface"),
                                troughcolor=_P("surface"))
        self._canvas.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self._canvas, bg=bg)
        self._win  = self._canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",  self._on_inner)
        self._canvas.bind("<Configure>", self._on_canvas)
        self._canvas.bind("<Enter>", self._bind_mw)
        self._canvas.bind("<Leave>", self._unbind_mw)

    def _on_inner(self, _):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas(self, e):
        self._canvas.itemconfig(self._win, width=e.width)

    def _bind_mw(self, _):
        self._canvas.bind_all("<MouseWheel>", self._on_mw)
        self._canvas.bind_all("<Button-4>",   lambda _: self._canvas.yview_scroll(-1,"units"))
        self._canvas.bind_all("<Button-5>",   lambda _: self._canvas.yview_scroll(1,"units"))

    def _unbind_mw(self, _):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mw(self, e):
        self._canvas.yview_scroll(int(-1*(e.delta/120)), "units")


class UnlockScreen(tk.Frame):
    def __init__(self, parent, vault, on_unlock):
        super().__init__(parent, bg=_P("base"))
        self.vault = vault; self._cb = on_unlock
        self._build()

    def _build(self):
        center = tk.Frame(self, bg=_P("base"))
        center.place(relx=0.5, rely=0.46, anchor="center")

        _GoatLogo(center, size=80, bg=_P("base")).pack()
        tk.Label(center, text="GoatsPass",
                 bg=_P("base"), fg=_P("text"),
                 font=F(32, bold=True)).pack(pady=(8, 2))
        tk.Label(center, text="Менеджер паролей  ·  v1.0",
                 bg=_P("base"), fg=_P("text3"), font=F(10)).pack()
        tk.Frame(center, bg=_P("base"), height=28).pack()

        is_new = not self.vault.exists()
        card   = tk.Frame(center, bg=_P("elevated"),
                          padx=44, pady=34,
                          highlightthickness=1,
                          highlightbackground=_P("border2"))
        card.pack(ipadx=4)

        heading = "Создать хранилище" if is_new else "Добро пожаловать"
        tk.Label(card, text=heading,
                 bg=_P("elevated"), fg=_P("text"),
                 font=F(17, bold=True)).pack(pady=(0, 6))

        if is_new:
            tk.Label(card,
                     text="Мастер-пароль защищает всё хранилище.\nПотеряв его — данные восстановить невозможно.",
                     bg=_P("elevated"), fg=_P("text3"),
                     font=F(9), justify="center").pack(pady=(0, 18))
        else:
            tk.Frame(card, bg=_P("elevated"), height=14).pack()

        tk.Label(card, text="Мастер-пароль",
                 bg=_P("elevated"), fg=_P("text2"),
                 font=F(9, bold=True), anchor="w").pack(fill="x")

        pw_row = tk.Frame(card, bg=_P("elevated"))
        pw_row.pack(fill="x", pady=(4, 0))
        self._ep = _Entry(pw_row, show_char="●", width=26)
        self._ep.pack(side="left", fill="x", expand=True, ipady=9)

        self._show_pw = False
        def _toggle():
            self._show_pw = not self._show_pw
            if not self._ep._ph_on:
                self._ep.config(show="" if self._show_pw else "●")
        eye = tk.Label(pw_row, text="👁", bg=_P("panel2"),
                       fg=_P("text3"), cursor="hand2",
                       font=F(11), padx=10, pady=9)
        eye.pack(side="left", padx=(3, 0))
        eye.bind("<Button-1>", lambda _: _toggle())
        eye.bind("<Enter>", lambda _: eye.config(fg=_P("text2")))
        eye.bind("<Leave>", lambda _: eye.config(fg=_P("text3")))
        _tooltip(eye, "Показать/скрыть")

        self._ec = None
        if is_new:
            tk.Frame(card, bg=_P("elevated"), height=10).pack()
            tk.Label(card, text="Подтвердите пароль",
                     bg=_P("elevated"), fg=_P("text2"),
                     font=F(9, bold=True), anchor="w").pack(fill="x")
            self._ec = _Entry(card, show_char="●", width=26)
            self._ec.pack(fill="x", pady=(4, 0), ipady=9)
            self._ec.bind("<Return>", lambda _: self._submit())
            tk.Frame(card, bg=_P("elevated"), height=8).pack()
            self._sbar = _StrengthBar(card, width=300)
            self._sbar.pack(fill="x")
            self._slbl = tk.Label(card, text="",
                                   bg=_P("elevated"), fg=_P("text3"),
                                   font=F(8), anchor="w")
            self._slbl.pack(fill="x")
            self._ep.bind("<KeyRelease>", self._update_strength)

        self._ep.bind("<Return>", lambda _: self._submit())
        self._status = tk.Label(card, text="",
                                 bg=_P("elevated"), fg=_P("red"), font=F(9))
        self._status.pack(pady=(12, 0))

        if self.vault.fails >= MAX_FAIL:
            self._status.config(text="⛔  Слишком много попыток. Перезапустите.")
        else:
            tk.Frame(card, bg=_P("elevated"), height=8).pack()
            label = "🔐  Создать хранилище" if is_new else "🔓  Войти"
            _PrimaryBtn(card, label, self._submit, py=11).pack(fill="x")

        tk.Frame(center, bg=_P("base"), height=18).pack()
        enc = "Argon2id" if _HAS_ARGON2 else "PBKDF2-SHA256"
        tk.Label(center, text=f"AES-256-GCM  ·  {enc}  ·  Локально",
                 bg=_P("base"), fg=_P("text4"), font=F(8)).pack()
        if not is_new:
            tk.Label(center, text=str(self.vault.path),
                     bg=_P("base"), fg=_P("text4"), font=F(7)).pack(pady=(2,0))

    def _update_strength(self, _=None):
        pw = self._ep.get()
        if self._ep._ph_on or not pw:
            self._slbl.config(text=""); return
        sc, lbl, col = pw_strength(pw)
        self._sbar.update(pw)
        self._slbl.config(text=lbl, fg=col)

    def _submit(self):
        pw = self._ep.get()
        if self._ep._ph_on or not pw:
            self._status.config(text="Введите мастер-пароль"); return
        if not self.vault.exists():
            cf = (self._ec.get() if self._ec and not self._ec._ph_on else "")
            if len(pw) < 8:
                self._status.config(text="Минимум 8 символов"); return
            if pw != cf:
                self._status.config(text="Пароли не совпадают"); return
            self._status.config(text="Создаём хранилище…", fg=_P("text3"))
            self.update(); self.vault.create(pw); self._cb()
        else:
            self._status.config(text="Открываем…", fg=_P("text3"))
            self.update()
            if self.vault.unlock(pw):
                self._cb()
            else:
                left = max(0, MAX_FAIL - self.vault.fails)
                msg = (f"Неверный пароль. Осталось попыток: {left}"
                       if left else "⛔  Попытки исчерпаны. Перезапустите.")
                self._status.config(text=msg, fg=_P("red"))
                self._ep.delete(0, tk.END)


class EntryDialog(tk.Toplevel):
    def __init__(self, parent, vault, entry: dict = None):
        super().__init__(parent)
        self.vault = vault; self.entry = entry; self.result = None
        t = f"✏️  Изменить  ·  {entry['title']}" if entry else "➕  Новая запись"
        self.title(t)
        self.configure(bg=_P("base"))
        self.resizable(True, True)
        self._build()
        if entry: self._fill(entry)
        self._center(parent)
        self.update_idletasks()
        self.grab_set(); self.focus_set()

    def _build(self):
        hdr = tk.Frame(self, bg=_P("elevated"), padx=22, pady=16)
        hdr.pack(fill="x")
        icon = "✏️  Изменить запись" if self.entry else "➕  Новая запись"
        tk.Label(hdr, text=icon, bg=_P("elevated"), fg=_P("text"),
                 font=F(14, bold=True)).pack(side="left")

        sf = _ScrollFrame(self, bg=_P("base"))
        sf.pack(fill="both", expand=True)
        body = sf.inner

        def _lbl(text):
            tk.Label(body, text=text, bg=_P("base"), fg=_P("text2"),
                     font=F(9, bold=True), anchor="w"
                     ).pack(fill="x", padx=22, pady=(14, 0))

        def _inp(ph="", show_char="", width=0):
            e = _Entry(body, placeholder=ph, show_char=show_char, width=width)
            e.pack(fill="x", padx=22, pady=(4, 0), ipady=8)
            return e

        _lbl("Название  *")
        self._f_title = _inp("Gmail, ВКонтакте, Steam…")

        _lbl("Логин / Email")
        self._f_user = _inp("user@example.com")

        _lbl("Пароль  *")
        pw_row = tk.Frame(body, bg=_P("base"))
        pw_row.pack(fill="x", padx=22, pady=(4, 0))
        self._f_pw = _Entry(pw_row, show_char="●")
        self._f_pw.pack(side="left", fill="x", expand=True, ipady=8)

        self._pw_vis = False
        def _toggle_pw():
            self._pw_vis = not self._pw_vis
            if not self._f_pw._ph_on:
                self._f_pw.config(show="" if self._pw_vis else "●")

        def _gen_pw():
            pw = make_password(20)
            self._f_pw._ph_on = False; self._f_pw.delete(0, tk.END)
            self._f_pw.config(fg=_P("text"), show=""); self._f_pw.insert(0, pw)
            self._pw_vis = True; self._update_strength()

        def _gen_phrase():
            pw = make_passphrase(4)
            self._f_pw._ph_on = False; self._f_pw.delete(0, tk.END)
            self._f_pw.config(fg=_P("text"), show=""); self._f_pw.insert(0, pw)
            self._pw_vis = True; self._update_strength()

        for ico, act, tip in [("👁",_toggle_pw,"Показать/скрыть"),
                               ("⚡",_gen_pw,   "Случайный пароль"),
                               ("📝",_gen_phrase,"Фраза-пароль")]:
            b = tk.Label(pw_row, text=ico, bg=_P("panel2"), fg=_P("text3"),
                         font=F(11), padx=9, pady=8, cursor="hand2")
            b.pack(side="left", padx=(3,0))
            b.bind("<Button-1>", lambda _, a=act: a())
            b.bind("<Enter>",    lambda _, w=b: w.config(fg=_P("text2")))
            b.bind("<Leave>",    lambda _, w=b: w.config(fg=_P("text3")))
            _tooltip(b, tip)

        self._sbar = _StrengthBar(body)
        self._sbar.pack(fill="x", padx=22, pady=(6,0))
        self._slbl = tk.Label(body, text="", bg=_P("base"), fg=_P("text3"),
                               font=F(8), anchor="w")
        self._slbl.pack(fill="x", padx=22)
        self._f_pw.bind("<KeyRelease>", lambda _: self._update_strength())

        _lbl("URL / Сайт")
        self._f_url = _inp("https://example.com")

        _lbl("Категория")
        self._f_cat = _Entry(body, placeholder="Общее")
        self._f_cat.pack(fill="x", padx=22, pady=(4,0), ipady=8)

        cat_pills = tk.Frame(body, bg=_P("base"))
        cat_pills.pack(fill="x", padx=22, pady=(4,0))
        for cat in ["Общее","Работа","Финансы","Социальные сети","Почта","Игры"]:
            p = tk.Label(cat_pills, text=cat, bg=_P("panel2"), fg=_P("text3"),
                         font=F(8), padx=8, pady=3, cursor="hand2")
            p.pack(side="left", padx=(0,4))
            p.bind("<Button-1>", lambda _, c=cat: self._f_cat.set_value(c))
            p.bind("<Enter>", lambda _, lp=p: lp.config(fg=_P("text2"), bg=_P("border")))
            p.bind("<Leave>", lambda _, lp=p: lp.config(fg=_P("text3"), bg=_P("panel2")))

        _lbl("Теги  (через запятую)")
        self._f_tags = _inp("работа, важное, банк")

        _lbl("TOTP / 2FA секрет  (необязательно)")
        self._f_totp = _inp("JBSWY3DPEHPK3PXP")

        _lbl("Заметки")
        self._f_notes = tk.Text(body, bg=_P("panel"), fg=_P("text"),
                                 insertbackground=_P("text"),
                                 relief="flat", font=F(10),
                                 highlightthickness=1,
                                 highlightbackground=_P("border2"),
                                 highlightcolor=_P("blue"),
                                 height=4, width=1)
        self._f_notes.pack(fill="x", padx=22, pady=(4,16), ipady=6)

        if self.entry and self.entry.get("history"):
            _divider(body, padx=22, pady=4)
            tk.Label(body, text="История паролей", bg=_P("base"), fg=_P("text2"),
                     font=F(9, bold=True), anchor="w").pack(fill="x", padx=22, pady=(8,4))
            hw = tk.Frame(body, bg=_P("elevated"),
                          highlightthickness=1, highlightbackground=_P("border"))
            hw.pack(fill="x", padx=22, pady=(0,16))
            for h in reversed(self.entry["history"][-5:]):
                r = tk.Frame(hw, bg=_P("elevated"))
                r.pack(fill="x")
                tk.Label(r, text="●" * min(len(h.get("pw","")),24),
                         bg=_P("elevated"), fg=_P("text3"),
                         font=F(9, mono=True), padx=12, pady=6).pack(side="left")
                tk.Label(r, text=h.get("when","")[:10],
                         bg=_P("elevated"), fg=_P("text3"),
                         font=F(8), padx=10).pack(side="right")

        _divider(self)
        foot = tk.Frame(self, bg=_P("surface"), padx=20, pady=12)
        foot.pack(fill="x")
        _Btn(foot, "Отмена", self.destroy,
             bg=_P("panel"), hover=_P("border2"), py=8).pack(side="right", padx=(6,0))
        _PrimaryBtn(foot, "💾  Сохранить", self._save, py=8).pack(side="right")

    def _update_strength(self):
        pw = self._f_pw.get()
        if self._f_pw._ph_on or not pw:
            self._slbl.config(text=""); return
        sc, lbl, col = pw_strength(pw)
        self._sbar.update(pw)
        bits = entropy_bits(pw)
        self._slbl.config(text=f"{lbl}  ·  {bits} бит энтропии", fg=col)

    def _fill(self, e: dict):
        for field, key in [(self._f_title,"title"),(self._f_user,"username"),
                           (self._f_url,"url"),(self._f_cat,"category")]:
            v = e.get(key,"")
            if v: field.set_value(v)
        pw = e.get("password","")
        self._f_pw._ph_on = False; self._f_pw.delete(0, tk.END)
        self._f_pw.config(fg=_P("text"), show="●"); self._f_pw.insert(0, pw)
        tags = e.get("tags",[])
        if tags: self._f_tags.set_value(", ".join(tags))
        totp = e.get("totp","")
        if totp: self._f_totp.set_value(totp)
        notes = e.get("notes","")
        if notes: self._f_notes.insert("1.0", notes)
        self._update_strength()

    def _save(self):
        title = self._f_title.value().strip()
        pw    = self._f_pw.get() if not self._f_pw._ph_on else ""
        if not title:
            messagebox.showwarning("Ошибка", "Введите название записи.", parent=self); return
        if not pw:
            messagebox.showwarning("Ошибка", "Введите пароль.", parent=self); return
        raw = self._f_tags.value().strip()
        tags = [t.strip() for t in raw.split(",") if t.strip()] if raw else []
        self.result = {
            "title":    title,
            "username": self._f_user.value(),
            "password": pw,
            "url":      self._f_url.value(),
            "category": self._f_cat.value() or "Общее",
            "tags":     tags,
            "totp":     self._f_totp.value(),
            "notes":    self._f_notes.get("1.0", tk.END).strip(),
        }
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        w, h = 520, 680
        self.geometry(f"{w}x{h}")
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")


class GeneratorDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Генератор паролей")
        self.configure(bg=_P("base"))
        self.resizable(False, False)
        self._last_pw = ""
        self._build(); self._generate()
        self._center(parent)
        self.update_idletasks()
        self.grab_set(); self.focus_set()

    def _build(self):
        hdr = tk.Frame(self, bg=_P("elevated"), padx=22, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚡  Генератор паролей",
                 bg=_P("elevated"), fg=_P("text"),
                 font=F(14, bold=True)).pack(side="left")

        body = tk.Frame(self, bg=_P("base"), padx=24, pady=20)
        body.pack(fill="both", expand=True)

        mode_f = tk.Frame(body, bg=_P("panel2"),
                           highlightthickness=1, highlightbackground=_P("border2"))
        mode_f.pack(fill="x", pady=(0,14))
        self._mode = tk.StringVar(value="random")
        for val, label in [("random","🎲  Случайный"),("phrase","📝  Фраза-пароль")]:
            tk.Radiobutton(mode_f, text=label, variable=self._mode, value=val,
                           command=self._generate,
                           bg=_P("panel2"), fg=_P("text3"),
                           selectcolor=_P("blue_dim"),
                           activebackground=_P("panel2"),
                           activeforeground=_P("text"),
                           indicatoron=False, relief="flat",
                           font=F(10), padx=14, pady=8, cursor="hand2"
                           ).pack(side="left", expand=True, fill="x")

        out_f = tk.Frame(body, bg=_P("elevated"),
                          highlightthickness=1, highlightbackground=_P("border2"))
        out_f.pack(fill="x", pady=(0,6))
        self._out_var = tk.StringVar(value="")
        tk.Label(out_f, textvariable=self._out_var,
                 bg=_P("elevated"), fg=_P("blue"),
                 font=F(14, mono=True),
                 padx=16, pady=16,
                 wraplength=360, justify="center").pack(fill="x")

        self._sbar = _StrengthBar(body)
        self._sbar.pack(fill="x", pady=(0,2))
        self._slbl = tk.Label(body, text="",
                               bg=_P("base"), fg=_P("text3"),
                               font=F(8), anchor="w")
        self._slbl.pack(fill="x")
        tk.Frame(body, bg=_P("base"), height=12).pack()

        row = tk.Frame(body, bg=_P("base")); row.pack(fill="x", pady=(0,8))
        tk.Label(row, text="Длина:", bg=_P("base"),
                 fg=_P("text2"), font=F(10)).pack(side="left")
        self._len_lbl = tk.Label(row, text="20", bg=_P("base"),
                                  fg=_P("blue"), font=F(11, bold=True), width=3)
        self._len_lbl.pack(side="right")
        self._len_var = tk.IntVar(value=20)
        tk.Scale(body, from_=8, to=64, orient="horizontal",
                 variable=self._len_var,
                 bg=_P("base"), fg=_P("text2"),
                 troughcolor=_P("panel"), activebackground=_P("blue"),
                 highlightthickness=0, bd=0, showvalue=False,
                 command=self._on_len).pack(fill="x", pady=(0,12))

        self._vars = {}
        for key, label, default in [
            ("upper",  "A–Z  Заглавные", True),
            ("lower",  "a–z  Строчные",  True),
            ("digits", "0–9  Цифры",     True),
            ("symbols","#!@  Символы",   True),
        ]:
            v = tk.BooleanVar(value=default); self._vars[key] = v
            tk.Checkbutton(body, text=label, variable=v,
                           command=self._generate,
                           bg=_P("base"), fg=_P("text2"),
                           selectcolor=_P("blue_dim"),
                           activebackground=_P("base"),
                           activeforeground=_P("text"),
                           font=F(10), anchor="w"
                           ).pack(fill="x", pady=1)

        tk.Frame(body, bg=_P("base"), height=10).pack()

        btn_r = tk.Frame(body, bg=_P("base")); btn_r.pack(fill="x")
        _PrimaryBtn(btn_r, "🔄  Новый", self._generate, py=9
                    ).pack(side="left", fill="x", expand=True, padx=(0,4))
        _Btn(btn_r, "📋  Копировать", self._copy,
             bg=_P("panel"), hover=_P("border2"), py=9
             ).pack(side="left", fill="x", expand=True)

        self._copy_status = tk.Label(body, text="",
                                      bg=_P("base"), fg=_P("green"), font=F(9))
        self._copy_status.pack(pady=(8,0))

        _divider(self)
        foot = tk.Frame(self, bg=_P("surface"), padx=20, pady=10)
        foot.pack(fill="x")
        _Btn(foot, "Закрыть", self.destroy,
             bg=_P("panel"), hover=_P("border2"), py=7).pack(side="right")

    def _on_len(self, v):
        self._len_lbl.config(text=str(int(float(v))))
        self._generate()

    def _generate(self, _=None):
        if self._mode.get() == "phrase":
            pw = make_passphrase(4)
        else:
            kw = {k: v.get() for k, v in self._vars.items()}
            pw = make_password(self._len_var.get(), **kw)
        self._last_pw = pw
        self._out_var.set(pw)
        sc, lbl, col = pw_strength(pw)
        self._sbar.update(pw)
        bits = entropy_bits(pw)
        self._slbl.config(text=f"{lbl}  ·  {bits} бит", fg=col)

    def _copy(self):
        if not self._last_pw: return
        self.clipboard_clear(); self.clipboard_append(self._last_pw); self.update()
        self._copy_status.config(text="✓  Скопировано в буфер обмена!")
        self.after(2500, lambda: self._copy_status.config(text=""))

    def _center(self, parent):
        self.update_idletasks()
        w, h = 420, 570
        self.geometry(f"{w}x{h}")
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")


class SecurityDialog(tk.Toplevel):
    def __init__(self, parent, vault):
        super().__init__(parent)
        self.title("Аудит безопасности")
        self.configure(bg=_P("base"))
        self.resizable(False, False)
        self._vault = vault
        self._build(); self._center(parent)
        self.update_idletasks()
        self.grab_set(); self.focus_set()

    def _build(self):
        hdr = tk.Frame(self, bg=_P("elevated"), padx=22, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🛡  Аудит безопасности",
                 bg=_P("elevated"), fg=_P("text"),
                 font=F(14, bold=True)).pack(side="left")

        sf = _ScrollFrame(self, bg=_P("base"))
        sf.pack(fill="both", expand=True)
        body = sf.inner

        st = self._vault.stats()
        tk.Frame(body, bg=_P("base"), height=16).pack()

        def _card(icon, label, value, color, note=""):
            c = tk.Frame(body, bg=_P("elevated"),
                         highlightthickness=1, highlightbackground=_P("border"))
            c.pack(fill="x", padx=20, pady=4)
            inner = tk.Frame(c, bg=_P("elevated"), padx=18, pady=14)
            inner.pack(fill="x")
            left = tk.Frame(inner, bg=_P("elevated"))
            left.pack(side="left")
            tk.Label(left, text=f"{icon}  {label}",
                     bg=_P("elevated"), fg=_P("text2"), font=F(10)).pack(anchor="w")
            if note:
                tk.Label(left, text=note,
                         bg=_P("elevated"), fg=_P("text3"), font=F(8)).pack(anchor="w")
            tk.Label(inner, text=str(value),
                     bg=_P("elevated"), fg=color, font=F(22, bold=True)).pack(side="right")

        _card("📦","Всего записей", st["total"], _P("text"))
        _card("⭐","Избранных",     st["fav"],   _P("amber"))
        _card("🔁","Дублирующихся паролей", st["dupes"],
              _P("red") if st["dupes"] > 0 else _P("green"),
              "Один пароль на нескольких сайтах — опасно")
        _card("⚠️","Слабых паролей", st["weak"],
              _P("red") if st["weak"] > 0 else _P("green"),
              "Оценка надёжности ниже 50%")
        _card("🕐","Старых паролей (90+ дней)", st["old"],
              _P("amber") if st["old"] > 0 else _P("green"),
              "Рекомендуется менять пароли каждые 90 дней")

        weak = [e for e in self._vault.entries
                if pw_strength(e.get("password",""))[0] < 50]
        if weak:
            tk.Frame(body, bg=_P("base"), height=8).pack()
            tk.Label(body, text="Записи со слабыми паролями:",
                     bg=_P("base"), fg=_P("text2"),
                     font=F(9, bold=True), anchor="w"
                     ).pack(fill="x", padx=20, pady=(4,4))
            for e in weak[:10]:
                sc, lbl, col = pw_strength(e.get("password",""))
                r = tk.Frame(body, bg=_P("elevated"),
                              highlightthickness=1, highlightbackground=_P("border"))
                r.pack(fill="x", padx=20, pady=2)
                inner = tk.Frame(r, bg=_P("elevated"), padx=16, pady=8)
                inner.pack(fill="x")
                tk.Label(inner, text=e["title"],
                         bg=_P("elevated"), fg=_P("text"), font=F(10)).pack(side="left")
                tk.Label(inner, text=lbl,
                         bg=_P("elevated"), fg=col, font=F(9)).pack(side="right")

        from collections import Counter
        pw_cnt = Counter(e["password"] for e in self._vault.entries if e.get("password"))
        dup_pws = {pw for pw, cnt in pw_cnt.items() if cnt > 1}
        dup_entries = [e for e in self._vault.entries if e.get("password") in dup_pws]
        if dup_entries:
            tk.Frame(body, bg=_P("base"), height=8).pack()
            tk.Label(body, text="Записи с одинаковыми паролями:",
                     bg=_P("base"), fg=_P("text2"),
                     font=F(9, bold=True), anchor="w"
                     ).pack(fill="x", padx=20, pady=(4,4))
            for e in dup_entries[:8]:
                r = tk.Frame(body, bg=_P("elevated"),
                              highlightthickness=1, highlightbackground=_P("red"))
                r.pack(fill="x", padx=20, pady=2)
                inner = tk.Frame(r, bg=_P("elevated"), padx=16, pady=8)
                inner.pack(fill="x")
                tk.Label(inner, text=e["title"],
                         bg=_P("elevated"), fg=_P("text"), font=F(10)).pack(side="left")
                tk.Label(inner, text="🔁  Дубликат",
                         bg=_P("elevated"), fg=_P("red"), font=F(9)).pack(side="right")

        tk.Frame(body, bg=_P("base"), height=16).pack()
        _divider(self)
        foot = tk.Frame(self, bg=_P("surface"), padx=20, pady=12)
        foot.pack(fill="x")
        _PrimaryBtn(foot, "Закрыть", self.destroy, py=8).pack(side="right")

    def _center(self, parent):
        self.update_idletasks()
        w, h = 500, 620
        self.geometry(f"{w}x{h}")
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")


class TOTPDialog(tk.Toplevel):
    def __init__(self, parent, secret: str):
        super().__init__(parent)
        self.title("2FA  —  Одноразовый код")
        self.configure(bg=_P("base"))
        self.resizable(False, False)
        self._secret = secret; self._timer_id = None
        self._build(); self._center(parent)
        self.update_idletasks()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        hdr = tk.Frame(self, bg=_P("elevated"), padx=22, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🔑  TOTP Код",
                 bg=_P("elevated"), fg=_P("text"),
                 font=F(13, bold=True)).pack(side="left")

        body = tk.Frame(self, bg=_P("base"), padx=36, pady=28)
        body.pack(fill="both", expand=True)

        code_f = tk.Frame(body, bg=_P("elevated"),
                           highlightthickness=1, highlightbackground=_P("border2"))
        code_f.pack(fill="x")
        self._code_var = tk.StringVar(value="------")
        tk.Label(code_f, textvariable=self._code_var,
                 bg=_P("elevated"), fg=_P("green"),
                 font=F(42, bold=True, mono=True),
                 padx=20, pady=22).pack()

        self._timer_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._timer_var,
                 bg=_P("base"), fg=_P("text3"), font=F(9)).pack(pady=(10,0))

        self._prog = tk.Canvas(body, height=5,
                                bg=_P("border"), highlightthickness=0)
        self._prog.pack(fill="x", pady=(4,18))

        self._copy_btn = _PrimaryBtn(body, "📋  Копировать", self._copy, py=10)
        self._copy_btn.pack(fill="x", pady=(0,8))
        _Btn(body, "Закрыть", self._on_close,
             bg=_P("panel"), hover=_P("border2"), py=8).pack(fill="x")
        self._refresh()

    def _refresh(self):
        try:
            code, rem = _totp(self._secret)
            self._code_var.set(code)
            self._timer_var.set(f"⏱  Действителен ещё {rem} сек")
            self._prog.delete("all")
            w = self._prog.winfo_width() or 300
            frac = rem / 30
            col  = _P("green") if frac > 0.4 else _P("amber") if frac > 0.2 else _P("red")
            self._prog.create_rectangle(0, 0, int(w * frac), 5, fill=col, outline="")
        except Exception as e:
            self._code_var.set("ОШИБКА"); self._timer_var.set(str(e))
        self._timer_id = self.after(1000, self._refresh)

    def _copy(self):
        code = self._code_var.get()
        self.clipboard_clear(); self.clipboard_append(code); self.update()
        self._copy_btn.config(text="✓  Скопировано!")
        self.after(2000, lambda: self._copy_btn.config(text="📋  Копировать"))

    def _on_close(self):
        if self._timer_id: self.after_cancel(self._timer_id)
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        w, h = 360, 360
        self.geometry(f"{w}x{h}")
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, vault):
        super().__init__(parent)
        self.title("Настройки")
        self.configure(bg=_P("base"))
        self.resizable(False, False)
        self._vault = vault
        self._build(); self._center(parent)
        self.update_idletasks()
        self.grab_set(); self.focus_set()

    def _build(self):
        hdr = tk.Frame(self, bg=_P("elevated"), padx=22, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙️  Настройки",
                 bg=_P("elevated"), fg=_P("text"),
                 font=F(14, bold=True)).pack(side="left")

        sf = _ScrollFrame(self, bg=_P("base"))
        sf.pack(fill="both", expand=True)
        body = sf.inner

        def _section(title):
            tk.Frame(body, bg=_P("base"), height=16).pack()
            tk.Label(body, text=title.upper(),
                     bg=_P("base"), fg=_P("text3"),
                     font=F(8, bold=True), anchor="w"
                     ).pack(fill="x", padx=22)
            tk.Frame(body, bg=_P("border"), height=1).pack(fill="x", padx=22, pady=(4,0))

        def _card_row(text, note=""):
            row = tk.Frame(body, bg=_P("elevated"),
                           highlightthickness=1, highlightbackground=_P("border"))
            row.pack(fill="x", padx=22, pady=(8,0))
            inner = tk.Frame(row, bg=_P("elevated"), padx=18, pady=13)
            inner.pack(fill="x")
            left = tk.Frame(inner, bg=_P("elevated"))
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=text, bg=_P("elevated"), fg=_P("text"),
                     font=F(10)).pack(anchor="w")
            if note:
                tk.Label(left, text=note, bg=_P("elevated"), fg=_P("text3"),
                         font=F(8)).pack(anchor="w")
            return inner

        _section("Безопасность")
        _card_row("🔒  Автоблокировка", note="5 минут бездействия")
        _card_row("📋  Буфер обмена",   note=f"Очищается через {CLIP_S} секунд")
        enc = "Argon2id" if _HAS_ARGON2 else "PBKDF2-SHA256 (600k итераций)"
        _card_row("🔐  Шифрование",     note=f"AES-256-GCM + {enc}")

        _section("Мастер-пароль")

        pw_card = tk.Frame(body, bg=_P("elevated"),
                           highlightthickness=1, highlightbackground=_P("border"))
        pw_card.pack(fill="x", padx=22, pady=(8,0))
        pw_body = tk.Frame(pw_card, bg=_P("elevated"), padx=18, pady=18)
        pw_body.pack(fill="x")

        tk.Label(pw_body, text="Изменить мастер-пароль",
                 bg=_P("elevated"), fg=_P("text"),
                 font=F(10, bold=True), anchor="w").pack(fill="x")
        tk.Label(pw_body,
                 text="Введите текущий пароль, затем дважды — новый.",
                 bg=_P("elevated"), fg=_P("text3"),
                 font=F(9), anchor="w").pack(fill="x", pady=(2,12))

        for attr, label in [("_old_pw","Текущий пароль"),
                             ("_new_pw","Новый пароль"),
                             ("_new_pw2","Подтвердите новый")]:
            tk.Label(pw_body, text=label, bg=_P("elevated"),
                     fg=_P("text2"), font=F(9, bold=True), anchor="w").pack(fill="x")
            e = _Entry(pw_body, show_char="●")
            e.pack(fill="x", pady=(3,10), ipady=8)
            setattr(self, attr, e)

        self._pw_status = tk.Label(pw_body, text="",
                                    bg=_P("elevated"), fg=_P("red"), font=F(9))
        self._pw_status.pack(anchor="w")
        tk.Frame(pw_body, bg=_P("elevated"), height=4).pack()
        _PrimaryBtn(pw_body, "🔑  Сменить пароль",
                    self._change_password, py=9).pack(fill="x")

        _section("Хранилище")
        vi = _card_row("Расположение файла")
        tk.Label(vi, text=str(self._vault.path),
                 bg=_P("elevated"), fg=_P("text3"),
                 font=F(8), wraplength=340, anchor="w"
                 ).pack(anchor="w", pady=(4,0))

        _section("О программе")
        about_card = tk.Frame(body, bg=_P("elevated"),
                               highlightthickness=1, highlightbackground=_P("border"))
        about_card.pack(fill="x", padx=22, pady=(8,0))
        ab = tk.Frame(about_card, bg=_P("elevated"), padx=18, pady=20)
        ab.pack(fill="x")

        logo_row = tk.Frame(ab, bg=_P("elevated"))
        logo_row.pack(fill="x")
        _GoatLogo(logo_row, size=44, bg=_P("elevated")).pack(side="left")
        tb = tk.Frame(logo_row, bg=_P("elevated"))
        tb.pack(side="left", padx=(14,0))
        tk.Label(tb, text="GoatsPass",
                 bg=_P("elevated"), fg=_P("text"),
                 font=F(15, bold=True), anchor="w").pack(anchor="w")
        tk.Label(tb, text=f"Версия {APP_VER}  ·  Локальный менеджер паролей",
                 bg=_P("elevated"), fg=_P("text3"),
                 font=F(9), anchor="w").pack(anchor="w")

        tk.Frame(ab, bg=_P("elevated"), height=14).pack()

        gh_row = tk.Frame(ab, bg=_P("elevated"))
        gh_row.pack(fill="x")
        tk.Label(gh_row, text="GitHub:", bg=_P("elevated"),
                 fg=_P("text3"), font=F(9)).pack(side="left")
        gh_lbl = tk.Label(gh_row, text=GITHUB,
                           bg=_P("elevated"), fg=_P("blue"),
                           font=F(9), cursor="hand2")
        gh_lbl.pack(side="left", padx=(6,0))
        gh_lbl.bind("<Button-1>", lambda _: webbrowser.open(GITHUB))
        gh_lbl.bind("<Enter>", lambda _: gh_lbl.config(fg=_P("blue_h")))
        gh_lbl.bind("<Leave>", lambda _: gh_lbl.config(fg=_P("blue")))

        tk.Frame(ab, bg=_P("elevated"), height=10).pack()
        tk.Label(ab, text="AES-256-GCM  ·  Argon2id  ·  Открытый исходный код  ·  MIT License",
                 bg=_P("elevated"), fg=_P("text3"),
                 font=F(8), anchor="w").pack(anchor="w")

        tk.Frame(body, bg=_P("base"), height=20).pack()

        _divider(self)
        foot = tk.Frame(self, bg=_P("surface"), padx=20, pady=12)
        foot.pack(fill="x")
        _Btn(foot, "Закрыть", self.destroy,
             bg=_P("panel"), hover=_P("border2"), py=8).pack(side="right")

    def _change_password(self):
        old  = self._old_pw.get()  if not self._old_pw._ph_on  else ""
        new  = self._new_pw.get()  if not self._new_pw._ph_on  else ""
        new2 = self._new_pw2.get() if not self._new_pw2._ph_on else ""
        if not old:
            self._pw_status.config(text="Введите текущий пароль",   fg=_P("red")); return
        if not new:
            self._pw_status.config(text="Введите новый пароль",     fg=_P("red")); return
        if len(new) < 8:
            self._pw_status.config(text="Минимум 8 символов",       fg=_P("red")); return
        if new != new2:
            self._pw_status.config(text="Пароли не совпадают",      fg=_P("red")); return
        self._pw_status.config(text="Обновляем…", fg=_P("text3")); self.update()
        if self._vault.change_master(old, new):
            for e in (self._old_pw, self._new_pw, self._new_pw2):
                e.delete(0, tk.END)
            self._pw_status.config(text="✓  Пароль успешно изменён", fg=_P("green"))
        else:
            self._pw_status.config(text="✗  Неверный текущий пароль", fg=_P("red"))

    def _center(self, parent):
        self.update_idletasks()
        w, h = 500, 680
        self.geometry(f"{w}x{h}")
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")


class GoatsPass(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GoatsPass  v1.0")
        self.configure(bg=_P("base"))
        self.minsize(960, 580)
        self.geometry("1160x720")
        self._set_icon()

        self.vault       = Vault()
        self._cur_id     = None
        self._filt       = []
        self._clip_token = None
        self._clip_lbl   = None

        self._show_unlock()
        self.after(12000, self._tick)

    def _set_icon(self):
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            try:
                img = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, img)
                self._icon_img = img
                return
            except Exception:
                pass
        try:
            img = tk.PhotoImage(width=32, height=32)
            c = _P("blue").lstrip("#")
            r, g, b = int(c[0:2],16), int(c[2:4],16), int(c[4:6],16)
            col = f"#{r:02x}{g:02x}{b:02x}"
            for y in range(18, 28):
                for x in range(6, 26): img.put(col, to=(x, y))
            for y in range(4, 18):
                for x in range(10, 22): img.put(col, to=(x, y))
            for i in range(5):
                img.put(col, to=(10-i, 2+i))
                img.put(col, to=(21+i, 2+i))
            self.iconphoto(True, img)
            self._icon_img = img
        except Exception:
            pass

    def _clear(self):
        for w in self.winfo_children(): w.destroy()

    def _show_unlock(self):
        self._clear()
        UnlockScreen(self, self.vault, self._show_main).pack(fill="both", expand=True)

    def _show_main(self):
        self._clear()
        self._build_main()

    def _tick(self):
        if self.vault.idle():
            messagebox.showinfo("GoatsPass", "Хранилище заблокировано из-за неактивности.")
            self.vault.lock(); self._show_unlock()
        else:
            self.after(12000, self._tick)

    def _build_main(self):
        top = tk.Frame(self, bg=_P("topbar"), height=54)
        top.pack(fill="x"); top.pack_propagate(False)
        tk.Frame(self, bg=_P("border"), height=1).pack(fill="x")

        logo_f = tk.Frame(top, bg=_P("topbar"))
        logo_f.pack(side="left", padx=(14,0))
        _GoatLogo(logo_f, size=32, bg=_P("topbar")).pack(side="left")
        tk.Label(logo_f, text="GoatsPass",
                 bg=_P("topbar"), fg=_P("text"),
                 font=F(13, bold=True)).pack(side="left", padx=(8,0))
        tk.Label(logo_f, text="v1.0",
                 bg=_P("topbar"), fg=_P("text3"),
                 font=F(9)).pack(side="left", padx=(4,0))

        sw = tk.Frame(top, bg=_P("topbar"))
        sw.pack(side="left", padx=20, fill="x", expand=True, pady=10)
        self._search_entry = _Entry(sw, placeholder="🔍  Поиск записей…")
        self._search_entry.pack(fill="x", ipady=6)
        self._search_entry.bind("<KeyRelease>", self._on_search)

        icon_f = tk.Frame(top, bg=_P("topbar"))
        icon_f.pack(side="right", padx=6)
        for ico, tip, cmd in [
            ("⚡","Генератор паролей", self._open_generator),
            ("🛡","Аудит безопасности",self._open_security),
            ("⚙️","Настройки",         self._open_settings),
            ("🔒","Заблокировать",     self._lock),
        ]:
            b = tk.Label(icon_f, text=ico,
                         bg=_P("topbar"), fg=_P("text3"),
                         font=F(14), padx=10, pady=15, cursor="hand2")
            b.pack(side="left")
            b.bind("<Enter>", lambda _, w=b: w.config(fg=_P("text"), bg=_P("panel")))
            b.bind("<Leave>", lambda _, w=b: w.config(fg=_P("text3"), bg=_P("topbar")))
            b.bind("<Button-1>", lambda _, c=cmd: c())
            _tooltip(b, tip)

        body = tk.Frame(self, bg=_P("base"))
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=_P("sidebar"), width=270)
        sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)
        tk.Frame(body, bg=_P("border"), width=1).pack(side="left", fill="y")

        sb_hdr = tk.Frame(sidebar, bg=_P("sidebar"), padx=12, pady=10)
        sb_hdr.pack(fill="x")

        tab_row = tk.Frame(sb_hdr, bg=_P("panel2"),
                           highlightthickness=1, highlightbackground=_P("border"))
        tab_row.pack(fill="x", pady=(0,6))
        self._tab = tk.StringVar(value="all")
        for val, label, tip in [("all","Все","Все записи"),
                                 ("fav","★  Избранные","Только избранные"),
                                 ("weak","⚠","Слабые пароли")]:
            rb = tk.Radiobutton(tab_row, text=label, variable=self._tab, value=val,
                                command=self._on_search,
                                bg=_P("panel2"), fg=_P("text3"),
                                selectcolor=_P("blue_dim"),
                                activebackground=_P("panel2"),
                                activeforeground=_P("text"),
                                indicatoron=False, relief="flat",
                                font=F(9), padx=8, pady=5, cursor="hand2")
            rb.pack(side="left", expand=True, fill="x")
            _tooltip(rb, tip)

        self._count_lbl = tk.Label(sb_hdr, text="0 записей",
                                    bg=_P("sidebar"), fg=_P("text3"),
                                    font=F(8), anchor="w")
        self._count_lbl.pack(fill="x", pady=(2,0))

        self._cat_var   = tk.StringVar(value="")
        self._cat_frame = tk.Frame(sidebar, bg=_P("sidebar"))
        self._cat_frame.pack(fill="x", padx=12, pady=(0,6))
        self._build_cat_filter()

        _divider(sidebar)

        list_w = tk.Frame(sidebar, bg=_P("sidebar"))
        list_w.pack(fill="both", expand=True)
        list_sb = tk.Scrollbar(list_w, orient="vertical",
                               bg=_P("sidebar"), troughcolor=_P("sidebar"), width=5)
        self._listbox = tk.Listbox(
            list_w, bg=_P("sidebar"), fg=_P("text"),
            selectbackground=_P("sel"), selectforeground=_P("sel_fg"),
            activestyle="none", relief="flat", bd=0,
            font=F(10), highlightthickness=0,
            yscrollcommand=list_sb.set)
        list_sb.config(command=self._listbox.yview)
        list_sb.pack(side="right", fill="y")
        self._listbox.pack(side="left", fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)
        self._listbox.bind("<Double-Button-1>", lambda _: self._edit_entry())

        _divider(sidebar)
        sb_foot = tk.Frame(sidebar, bg=_P("sidebar"), padx=12, pady=8)
        sb_foot.pack(fill="x")
        self._sidebar_status = tk.Label(sb_foot, text="",
                                         bg=_P("sidebar"), fg=_P("text3"),
                                         font=F(8), anchor="w")
        self._sidebar_status.pack(fill="x")

        right = tk.Frame(body, bg=_P("base"))
        right.pack(fill="both", expand=True)
        self._detail_frame = tk.Frame(right, bg=_P("base"))
        self._detail_frame.pack(fill="both", expand=True)

        self._fab = _FAB(right, self._add_entry, size=52)
        self._fab.place(relx=1.0, rely=1.0, anchor="se", x=-22, y=-22)

        self._refresh_list()
        self._show_empty_detail()

    def _build_cat_filter(self):
        for w in self._cat_frame.winfo_children(): w.destroy()
        cats = [""] + self.vault.get_categories()
        if len(cats) <= 2: return
        tk.Label(self._cat_frame, text="Категория:",
                 bg=_P("sidebar"), fg=_P("text3"),
                 font=F(8), anchor="w").pack(fill="x")
        om = tk.OptionMenu(self._cat_frame, self._cat_var,
                           *cats, command=lambda _: self._on_search())
        om.config(bg=_P("panel2"), fg=_P("text2"),
                  activebackground=_P("panel"), activeforeground=_P("text"),
                  relief="flat", font=F(9), highlightthickness=0, bd=0)
        om["menu"].config(bg=_P("panel2"), fg=_P("text2"),
                          activebackground=_P("sel"),
                          activeforeground=_P("sel_fg"),
                          relief="flat")
        om.pack(fill="x")

    def _get_filtered(self) -> list:
        q   = self._search_entry.value().strip()
        res = self.vault.search(q)
        t   = self._tab.get()
        if t == "fav":  res = [e for e in res if e.get("favorite")]
        if t == "weak": res = [e for e in res if pw_strength(e.get("password",""))[0] < 50]
        cat = self._cat_var.get()
        if cat: res = [e for e in res if e.get("category","") == cat]
        return sorted(res, key=lambda e: (not e.get("favorite",False), e["title"].lower()))

    def _refresh_list(self, keep_selection=False):
        self._filt = self._get_filtered()
        self._listbox.delete(0, tk.END)
        for e in self._filt:
            star = "★  " if e.get("favorite") else "    "
            cat  = f"  [{e.get('category','Общее')}]"
            self._listbox.insert(tk.END, f"{star}{e['title']}{cat}")
        total = len(self.vault.entries)
        shown = len(self._filt)
        self._count_lbl.config(
            text=f"{shown} из {total}" if shown != total else f"{total} записей")
        if keep_selection and self._cur_id:
            for i, e in enumerate(self._filt):
                if e["id"] == self._cur_id:
                    self._listbox.selection_set(i)
                    self._listbox.see(i); break

    def _on_search(self, *_):
        self.vault.touch(); self._refresh_list()

    def _on_select(self, _=None):
        sel = self._listbox.curselection()
        if not sel: return
        e = self._filt[sel[0]]; self._cur_id = e["id"]
        self._show_detail(e); self.vault.touch()

    def _show_empty_detail(self):
        for w in self._detail_frame.winfo_children(): w.destroy()
        c = tk.Frame(self._detail_frame, bg=_P("base"))
        c.place(relx=0.5, rely=0.44, anchor="center")
        _GoatLogo(c, size=68, bg=_P("base")).pack()
        tk.Label(c, text="Выберите запись из списка\n\nили нажмите  +  чтобы добавить новую",
                 bg=_P("base"), fg=_P("text3"),
                 font=F(12), justify="center").pack(pady=(16,0))

    def _show_detail(self, entry: dict):
        for w in self._detail_frame.winfo_children(): w.destroy()
        self.vault.touch(); self._clip_lbl = None

        hdr = tk.Frame(self._detail_frame, bg=_P("elevated"), padx=24, pady=16)
        hdr.pack(fill="x")

        lhdr = tk.Frame(hdr, bg=_P("elevated"))
        lhdr.pack(side="left", fill="x", expand=True)
        star = "★  " if entry.get("favorite") else ""
        tk.Label(lhdr, text=f"{star}{entry['title']}",
                 bg=_P("elevated"), fg=_P("text"),
                 font=F(18, bold=True), anchor="w").pack(anchor="w")

        meta = tk.Frame(lhdr, bg=_P("elevated"))
        meta.pack(anchor="w", pady=(3,0))
        cat = entry.get("category","Общее")
        tk.Label(meta, text=cat, bg=_P("blue_dim"), fg=_P("blue"),
                 font=F(8), padx=8, pady=2).pack(side="left")

        btn_row = tk.Frame(hdr, bg=_P("elevated"))
        btn_row.pack(side="right")

        def _toggle_fav():
            self.vault.toggle_fav(entry["id"])
            ne = next((x for x in self.vault.entries if x["id"] == entry["id"]), None)
            if ne: self._refresh_list(True); self._show_detail(ne)

        fav_col = _P("amber") if entry.get("favorite") else _P("text3")
        b_fav = tk.Label(btn_row, text="★",
                          bg=_P("elevated"), fg=fav_col,
                          font=F(16), padx=8, pady=8, cursor="hand2")
        b_fav.pack(side="left")
        b_fav.bind("<Button-1>", lambda _: _toggle_fav())
        b_fav.bind("<Enter>",    lambda _: b_fav.config(fg=_P("amber")))
        b_fav.bind("<Leave>",    lambda _: b_fav.config(fg=fav_col))
        _tooltip(b_fav, "Избранное")

        b_edit = _Btn(btn_row, "✏  Изменить", self._edit_entry,
                      bg=_P("panel"), hover=_P("border2"), py=7)
        b_edit.pack(side="left", padx=(4,0))

        b_del = _Btn(btn_row, "🗑  Удалить",
                     lambda: self._delete_entry(entry["id"]),
                     bg=_P("panel"), fg=_P("red"), hover="#2a1313", py=7)
        b_del.pack(side="left", padx=(4,0))

        _divider(self._detail_frame)

        sf = _ScrollFrame(self._detail_frame, bg=_P("base"))
        sf.pack(fill="both", expand=True)
        body = sf.inner

        self._clip_lbl = tk.Label(body, text="",
                                   bg=_P("base"), fg=_P("green"),
                                   font=F(9), anchor="w")
        self._clip_lbl.pack(fill="x", padx=24, pady=(12,0))

        def _copy(val: str, name: str):
            self.clipboard_clear(); self.clipboard_append(val); self.update()
            if self._clip_lbl:
                self._clip_lbl.config(
                    text=f"✓  {name} скопирован  —  буфер очистится через {CLIP_S} сек")
            if self._clip_token: self.after_cancel(self._clip_token)
            self._clip_token = self.after(CLIP_S * 1000, self._clear_clip)

        def _field_row(label: str, value: str, secret=False, url=False):
            if not value: return
            row = tk.Frame(body, bg=_P("elevated"),
                           highlightthickness=1, highlightbackground=_P("border"))
            row.pack(fill="x", padx=24, pady=3)
            inner = tk.Frame(row, bg=_P("elevated"), padx=16, pady=10)
            inner.pack(fill="x")
            tk.Label(inner, text=label, bg=_P("elevated"), fg=_P("text3"),
                     font=F(9), width=11, anchor="w").pack(side="left")
            disp   = "●" * min(len(value), 30) if secret else value
            vis    = [False]
            val_lbl = tk.Label(inner, text=disp, bg=_P("elevated"), fg=_P("text"),
                                font=F(11, mono=secret), anchor="w")
            val_lbl.pack(side="left", fill="x", expand=True)
            actions = tk.Frame(inner, bg=_P("elevated"))
            actions.pack(side="right")

            cb = tk.Label(actions, text="📋", bg=_P("elevated"), fg=_P("text3"),
                           font=F(10), padx=6, cursor="hand2")
            cb.pack(side="right")
            cb.bind("<Button-1>", lambda _: _copy(value, label))
            cb.bind("<Enter>",    lambda _: cb.config(fg=_P("text2")))
            cb.bind("<Leave>",    lambda _: cb.config(fg=_P("text3")))
            _tooltip(cb, "Копировать")

            if secret:
                def _toggle(lb=val_lbl, v=value, s=vis):
                    s[0] = not s[0]
                    lb.config(text=v if s[0] else "●" * min(len(v),30))
                eye = tk.Label(actions, text="👁", bg=_P("elevated"), fg=_P("text3"),
                               font=F(10), padx=6, cursor="hand2")
                eye.pack(side="right")
                eye.bind("<Button-1>", lambda _: _toggle())
                eye.bind("<Enter>",    lambda _: eye.config(fg=_P("text2")))
                eye.bind("<Leave>",    lambda _: eye.config(fg=_P("text3")))
                _tooltip(eye, "Показать/скрыть")

            if url and value.startswith("http"):
                gl = tk.Label(actions, text="🌐", bg=_P("elevated"), fg=_P("sky"),
                               font=F(10), padx=6, cursor="hand2")
                gl.pack(side="right")
                gl.bind("<Button-1>", lambda _, u=value: webbrowser.open(u))
                _tooltip(gl, "Открыть в браузере")

        _field_row("Логин",  entry.get("username",""))
        _field_row("Пароль", entry.get("password",""), secret=True)
        _field_row("URL",    entry.get("url",""), url=True)

        tags = entry.get("tags",[])
        if tags:
            tr = tk.Frame(body, bg=_P("base"))
            tr.pack(fill="x", padx=24, pady=3)
            tk.Label(tr, text="Теги", bg=_P("base"), fg=_P("text3"),
                     font=F(9), width=11, anchor="w").pack(side="left")
            for t in tags:
                tk.Label(tr, text=t, bg=_P("blue_dim"), fg=_P("sky"),
                         font=F(9), padx=8, pady=2
                         ).pack(side="left", padx=(0,4))

        totp = entry.get("totp","").strip()
        if totp:
            tr = tk.Frame(body, bg=_P("elevated"),
                          highlightthickness=1, highlightbackground=_P("border"))
            tr.pack(fill="x", padx=24, pady=3)
            inner = tk.Frame(tr, bg=_P("elevated"), padx=16, pady=10)
            inner.pack(fill="x")
            tk.Label(inner, text="2FA", bg=_P("elevated"), fg=_P("text3"),
                     font=F(9), width=11, anchor="w").pack(side="left")
            btn_t = tk.Label(inner, text="🔑  Показать код TOTP",
                              bg=_P("elevated"), fg=_P("blue"),
                              font=F(10), cursor="hand2")
            btn_t.pack(side="left")
            btn_t.bind("<Button-1>", lambda _, s=totp: TOTPDialog(self, s))
            btn_t.bind("<Enter>", lambda _: btn_t.config(fg=_P("blue_h")))
            btn_t.bind("<Leave>", lambda _: btn_t.config(fg=_P("blue")))

        pw = entry.get("password","")
        if pw:
            sc, lbl_txt, col = pw_strength(pw)
            bits = entropy_bits(pw)
            _divider(body, padx=24, pady=4)
            sr = tk.Frame(body, bg=_P("base"))
            sr.pack(fill="x", padx=24, pady=(6,2))
            tk.Label(sr, text="Надёжность:",
                     bg=_P("base"), fg=_P("text3"), font=F(9)).pack(side="left")
            tk.Label(sr, text=lbl_txt,
                     bg=_P("base"), fg=col, font=F(9, bold=True)
                     ).pack(side="left", padx=(6,0))
            tk.Label(sr, text=f"  ·  {bits} бит",
                     bg=_P("base"), fg=_P("text3"), font=F(8)).pack(side="left")
            bar = _StrengthBar(body)
            bar.pack(fill="x", padx=24, pady=(0,8))
            self.after(60, lambda b=bar, p=pw: b.update(p))

        notes = entry.get("notes","").strip()
        if notes:
            _divider(body, padx=24, pady=4)
            tk.Label(body, text="Заметки", bg=_P("base"), fg=_P("text3"),
                     font=F(9), anchor="w").pack(anchor="w", padx=24, pady=(8,2))
            nb = tk.Text(body, bg=_P("elevated"), fg=_P("text2"),
                         relief="flat", font=F(10),
                         highlightthickness=1, highlightbackground=_P("border"),
                         height=min(6, notes.count("\n")+2), width=1)
            nb.pack(fill="x", padx=24, pady=(0,8))
            nb.insert("1.0", notes); nb.config(state="disabled")

        cr = entry.get("created","")[:10]
        mo = entry.get("modified","")[:10]
        _divider(body, padx=24, pady=4)
        tk.Label(body, text=f"Создано: {cr}   ·   Изменено: {mo}",
                 bg=_P("base"), fg=_P("text4"), font=F(8)
                 ).pack(anchor="w", padx=24, pady=(8,24))

    def _clear_clip(self):
        try:
            self.clipboard_clear(); self.update()
        except Exception: pass
        if self._clip_lbl: self._clip_lbl.config(text="")

    def _add_entry(self):
        dlg = EntryDialog(self, self.vault)
        self.wait_window(dlg)
        if dlg.result:
            e = self.vault.add(**dlg.result)
            self._cur_id = e["id"]
            self._build_cat_filter()
            self._refresh_list()
            self._show_detail(e)
            self._sidebar_status.config(text=f"✓  Добавлено: {e['title']}")
            self.after(3500, lambda: self._sidebar_status.config(text=""))

    def _edit_entry(self):
        if not self._cur_id: return
        entry = next((e for e in self.vault.entries if e["id"] == self._cur_id), None)
        if not entry: return
        dlg = EntryDialog(self, self.vault, entry)
        self.wait_window(dlg)
        if dlg.result:
            self.vault.update(self._cur_id, **dlg.result)
            updated = next(e for e in self.vault.entries if e["id"] == self._cur_id)
            self._build_cat_filter()
            self._refresh_list(True)
            self._show_detail(updated)

    def _delete_entry(self, eid: str):
        entry = next((e for e in self.vault.entries if e["id"] == eid), None)
        name  = entry["title"] if entry else "?"
        if not messagebox.askyesno(
                "Удалить запись?",
                f"Вы уверены, что хотите удалить\n«{name}»?\n\nЭто действие необратимо.",
                parent=self): return
        self.vault.delete(eid)
        self._cur_id = None
        self._build_cat_filter()
        self._refresh_list()
        self._show_empty_detail()

    def _lock(self):
        self.vault.lock(); self._cur_id = None; self._show_unlock()

    def _open_generator(self): GeneratorDialog(self)
    def _open_security(self):  SecurityDialog(self, self.vault)
    def _open_settings(self):  SettingsDialog(self, self.vault)


if __name__ == "__main__":
    app = GoatsPass()
    app.mainloop()
