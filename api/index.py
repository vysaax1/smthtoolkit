import os
import sys
import io
import zipfile
import random
import json
import hashlib
import requests
from datetime import datetime, timezone
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory, send_file

app = Flask(__name__)

VERSION = "3.0"
WATERMARK = "=" * 40 + "\n               SMTH©2026\n            PROPERTY OF SMTH\n" + "=" * 40 + "\n\n"

# ============================================================================
#                     WORD POOL (TIERED, CACHED)
# ============================================================================

_CORE = None
_EXT = None
_FALLBACK_NAMES = ["Adi", "Budi", "Citra", "Dewi", "Eka", "Fajar", "Gita"]

def _load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]

def get_core():
    global _CORE
    if _CORE is None:
        path = os.path.join(os.path.dirname(__file__), "words_core.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                _CORE = json.load(f)
        except Exception:
            _CORE = {"names": _FALLBACK_NAMES, "adjectives": [], "nouns": [],
                     "slang_prefix": [], "slang_core": [], "anime": [],
                     "short": [], "region_suffix": {}}
    return _CORE

def get_extended():
    global _EXT
    if _EXT is None:
        path = os.path.join(os.path.dirname(__file__), "words_extended.txt")
        _EXT = _load(path) or None
    return _EXT

# ============================================================================
#                     GAMERTAG ARCHETYPE ENGINE
# ============================================================================

BIRTH_YEARS_2D = [str(y)[-2:] for y in range(1985, 2012)]
TRYHARD_BASE = ["ProSweat", "CarryMe", "TryHard", "NoobMaster", "Sweaty",
                "AimGod", "Doge", "Chad", "Sigma", "Gamer", "Pro", "Epic"]
TRYHARD_TAGS = ["_YT", "_TT", "_OP", "_69", "_420", "_007", "_Pro",
                "_God", "_King", "X", "99", "21"]

LEET = {'a':'4','e':'3','i':'1','o':'0','s':'5','t':'7','g':'9'}

def leetify(w):
    return ''.join(LEET.get(c.lower(), c) if c.isalpha() else c for c in w)

def vary_case(w):
    r = random.random()
    if r < 0.35: return w.capitalize()
    if r < 0.55: return w.lower()
    if r < 0.72: return w.upper()
    if r < 0.85: return w[:1].lower() + w[1:]
    return w

ARCHETYPES = [
    ("name_year", 25), ("compound", 20), ("edgy", 12),
    ("tryhard", 10), ("slang", 10), ("aesthetic", 8),
    ("leet", 5), ("weeb", 5), ("numberish", 3), ("extended", 2),
]

def gen_gamertag(region="indonesia"):
    cats = get_core()
    suffixes = cats.get("region_suffix", {}).get(region, [""])
    names  = cats.get("names") or _FALLBACK_NAMES
    adjs   = cats.get("adjectives") or []
    nouns  = cats.get("nouns") or []
    slang_p = cats.get("slang_prefix") or [""]
    slang_c = cats.get("slang_core") or []
    anime  = cats.get("anime") or []
    shorts = cats.get("short") or []

    for _ in range(60):
        arch = random.choices([a[0] for a in ARCHETYPES],
                              weights=[a[1] for a in ARCHETYPES])[0]
        u = None
        try:
            if arch == "name_year":
                u = random.choice(names) + random.choice(BIRTH_YEARS_2D)
            elif arch == "compound":
                u = random.choice(adjs) + random.choice(nouns)
                if random.random() < 0.20:
                    u += random.choice(BIRTH_YEARS_2D)
            elif arch == "edgy":
                core = random.choice(nouns + adjs)
                u = random.choice([f"xX_{core}_Xx", f"_{core}_",
                                   f"-{core}-", f"xX{core}Xx"])
            elif arch == "tryhard":
                u = random.choice(TRYHARD_BASE) + random.choice(TRYHARD_TAGS)
            elif arch == "slang" and region == "indonesia" and slang_c:
                u = random.choice(slang_p + [""]) + random.choice(slang_c)
            elif arch == "aesthetic" and shorts:
                w = random.choice(shorts)
                u = random.choice(["_", "-", ""]) + w + \
                    random.choice(["_", "", "77", "99"])
            elif arch == "leet" and adjs and nouns:
                u = leetify(random.choice(adjs) + random.choice(nouns))
            elif arch == "weeb" and anime:
                w = random.choice(anime)
                u = random.choice(["_", "-", ""]) + w + \
                    random.choice(["_", "99", "07", "-kun"])
            elif arch == "numberish" and shorts:
                u = random.choice(["404", "007", "88", "99", "123"]) + \
                    random.choice(shorts)
            elif arch == "extended":
                ext = get_extended()
                if ext:
                    u = random.choice(ext).capitalize()
                    if random.random() < 0.4:
                        u += random.choice(BIRTH_YEARS_2D)
                else:
                    u = random.choice(adjs or names) + random.choice(suffixes)
        except (IndexError, KeyError):
            continue

        if not u:
            continue
        u = vary_case(u)
        if 6 <= len(u) <= 20 and u.isascii():
            return u

    return "Player" + str(random.randint(10000, 99999))

# ============================================================================
#                     COMBO MODE (legacy)
# ============================================================================

def gen_combo(mode, region, pool):
    base = random.choice(pool).capitalize()
    if mode == "plain":    return base
    if mode == "2digit":   return f"{base}{random.randint(10, 99)}"
    if mode == "3digit":   return f"{base}{random.randint(100, 999)}"
    if mode == "4digit":   return f"{base}{random.randint(1000, 9999)}"
    if mode == "mix":
        return gen_combo(random.choice(["plain", "2digit", "3digit", "4digit"]),
                         region, pool)
    return base

def generate_usernames(mode, region, count):
    """mode: 'gamertag' | 'plain' | '2digit' | '3digit' | '4digit' | 'mix'"""
    out = set()
    max_attempts = count * 25
    attempts = 0

    if mode == "gamertag":
        while len(out) < count and attempts < max_attempts:
            attempts += 1
            u = gen_gamertag(region)
            if 6 <= len(u) <= 20:
                out.add(u)
    else:
        pool = get_extended() or get_core().get("names") or _FALLBACK_NAMES
        pool = [w for w in pool if 3 <= len(w) <= 15]
        while len(out) < count and attempts < max_attempts:
            attempts += 1
            u = gen_combo(mode, region, pool)
            if 6 <= len(u) <= 20:
                out.add(u)

    result = list(out)
    random.shuffle(result)
    return result

# ============================================================================
#                     HTTP API (existing + updated)
# ============================================================================

@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.json or {}
        mode     = data.get('mode', 'gamertag')
        region   = data.get('region', 'indonesia')
        count    = int(data.get('count', 10))
        if count <= 0 or count > 50000:
            return jsonify({"status": "error", "msg": "Jumlah harus 1-50000"})

        usernames = generate_usernames(mode, region, count)
        warning = None
        if len(usernames) < count:
            warning = (f"Kapasitas pool terbatas, hanya menghasilkan "
                       f"{len(usernames)}/{count} unik.")

        return jsonify({
            "status": "success",
            "total": len(usernames),
            "requested": count,
            "warning": warning,
            "data": usernames,
        })
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route('/api/check-duplicates', methods=['POST'])
def api_check_duplicates():
    try:
        text = (request.json or {}).get('text', '')
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        counts = Counter(lines)
        dupes = {k: v for k, v in counts.items() if v > 1}
        return jsonify({
            "status": "success",
            "total_lines": len(lines),
            "unique": len(counts),
            "dupes": len(dupes),
            "extra": sum(v - 1 for v in dupes.values()),
            "duplicate_list": [{"item": k, "count": v} for k, v in dupes.items()],
        })
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route('/api/split', methods=['POST'])
def api_split():
    try:
        data = request.json or {}
        text = data.get('text', '')
        chunk_size = int(data.get('chunkSize', 100))
        base_name = (data.get('filename') or 'split_result').strip()
        if chunk_size <= 0:
            return jsonify({"status": "error", "msg": "Chunk size > 0"})

        lines = text.splitlines(keepends=True)
        if not lines:
            return jsonify({"status": "error", "msg": "File kosong!"})

        total_parts = (len(lines) + chunk_size - 1) // chunk_size
        safe_name = "".join(c for c in base_name if c.isalnum() or c in "-_") \
                    or "split_result"

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            pad = max(3, len(str(total_parts)))
            for i in range(total_parts):
                chunk = lines[i * chunk_size:(i + 1) * chunk_size]
                name = f"{safe_name}_part_{i + 1:0{pad}d}.txt"
                zf.writestr(name, WATERMARK + "".join(chunk))
        buf.seek(0)

        resp = send_file(buf, mimetype='application/zip', as_attachment=True,
                         download_name=f"{safe_name}.zip")
        resp.headers['X-Total-Lines'] = str(len(lines))
        resp.headers['X-Total-Files'] = str(total_parts)
        resp.headers['X-Zip-Name']    = f"{safe_name}.zip"
        return resp
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route('/')
def index():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public_dir = os.path.join(base_dir, 'public')
    return send_from_directory('index.html')

# ============================================================================
#                     TELEGRAM BOT — WEBHOOK
# ============================================================================

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "smth-webhook-secret")
TG_API = f"https://api.telegram.org/bot{TG_TOKEN}"

# pending state in-memory (TTL 10 menit)
_PENDING = {}

def _clean_pending():
    now = datetime.now(timezone.utc).timestamp()
    for k in list(_PENDING):
        if now - _PENDING[k].get("ts", 0) > 600:
            _PENDING.pop(k, None)

def tg_call(method, **kwargs):
    if not TG_TOKEN:
        return {"ok": False, "error": "no token"}
    try:
        r = requests.post(f"{TG_API}/{method}", json=kwargs, timeout=15)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def tg_send(chat_id, text, markup=None, html=False):
    kw = {"chat_id": chat_id, "text": text,
          "parse_mode": "HTML" if html else None,
          "disable_web_page_preview": True}
    if markup: kw["reply_markup"] = markup
    return tg_call("sendMessage", **kw)

def tg_edit(chat_id, msg_id, text, markup=None, html=False):
    kw = {"chat_id": chat_id, "message_id": msg_id, "text": text,
          "parse_mode": "HTML" if html else None}
    if markup: kw["reply_markup"] = markup
    return tg_call("editMessageText", **kw)

def tg_answer_cb(cb_id, text=None):
    kw = {"callback_query_id": cb_id}
    if text: kw["text"] = text
    return tg_call("answerCallbackQuery", **kw)

def tg_send_doc(chat_id, filename, content, caption=None):
    files = {"document": (filename, content, "text/plain")}
    data = {"chat_id": chat_id}
    if caption: data["caption"] = caption
    try:
        r = requests.post(f"{TG_API}/sendDocument", files=files,
                          data=data, timeout=30)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def kb(rows):
    return {"inline_keyboard": rows}

# ── menu builders ──

def kb_main():
    return kb([
        [{"text": "⚡ Generate",      "callback_data": "menu:gen"},
         {"text": "🔍 Check Dupes",   "callback_data": "menu:dup"}],
        [{"text": "✂️ Split File",    "callback_data": "menu:split"},
         {"text": "ℹ️ Help",          "callback_data": "menu:help"}],
    ])

def kb_modes():
    return kb([
        [{"text": "🎮 Gamertag", "callback_data": "g:gamertag"}],
        [{"text": "Plain", "callback_data": "g:plain"},
         {"text": "+2",    "callback_data": "g:2digit"},
         {"text": "+3",    "callback_data": "g:3digit"},
         {"text": "+4",    "callback_data": "g:4digit"},
         {"text": "Mix",   "callback_data": "g:mix"}],
        [{"text": "⬅️ Menu", "callback_data": "menu:main"}],
    ])

def kb_regions(mode):
    return kb([
        [{"text": "🇮🇩 ID", "callback_data": f"r:{mode}:indonesia"},
         {"text": "🇵🇭 PH", "callback_data": f"r:{mode}:philippines"},
         {"text": "🇲🇾 MY", "callback_data": f"r:{mode}:malaysia"},
         {"text": "🇸🇬 SG", "callback_data": f"r:{mode}:singapore"}],
        [{"text": "⬅️ Mode", "callback_data": "menu:gen"}],
    ])

def kb_counts(mode, region):
    row = []
    for n in (50, 100, 500, 1000, 5000):
        row.append({"text": str(n), "callback_data": f"c:{mode}:{region}:{n}"})
    return kb([
        row[:3],
        row[3:],
        [{"text": "⬅️ Region", "callback_data": f"g:{mode}"}],
    ])

def kb_chunk(key):
    return kb([
        [{"text": "50",   "callback_data": f"s:{key}:50"},
         {"text": "100",  "callback_data": f"s:{key}:100"},
         {"text": "500",  "callback_data": f"s:{key}:500"},
         {"text": "1000", "callback_data": f"s:{key}:1000"}],
        [{"text": "❌ Cancel", "callback_data": "menu:main"}],
    ])

# ── command handlers ──

def handle_start(chat_id, user):
    name = user.get("first_name", "Player")
    text = (f"<b>👋 Halo, {name}!</b>\n\n"
            f"<b>SMTH Toolkit v{VERSION}</b>\n"
            f"Gamertag & combo generator + tools.\n\n"
            f"Pilih menu:")
    tg_send(chat_id, text, kb_main(), html=True)

def handle_help(chat_id):
    text = (
        "<b>📖 Cara Pakai</b>\n\n"
        "<b>⚡ Generate</b>\n"
        "1. Tap <b>Generate</b>\n"
        "2. Pilih mode (Gamertag/Combo)\n"
        "3. Pilih region\n"
        "4. Pilih jumlah\n"
        "5. Bot kirim file .txt\n\n"
        "<b>🔍 Check Dupes</b>\n"
        "Kirim file .txt atau paste text berisi list.\n\n"
        "<b>✂️ Split File</b>\n"
        "Kirim file .txt, lalu pilih ukuran per file.\n"
        "Bot kirim balik ZIP.\n\n"
        "<b>Commands</b>\n"
        "/start — menu utama\n"
        "/generate — mulai generate\n"
        "/checkdup — cek duplikat\n"
        "/split — split file\n"
        "/help — pesan ini"
    )
    tg_send(chat_id, text, kb_main(), html=True)

def handle_generate_flow(chat_id, msg_id=None):
    text = "<b>⚡ Generate</b>\n\nPilih <b>mode</b>:"
    if msg_id:
        tg_edit(chat_id, msg_id, text, kb_modes(), html=True)
    else:
        tg_send(chat_id, text, kb_modes(), html=True)

def do_generate(chat_id, mode, region, count):
    tg_send(chat_id, f"⏳ Generating {count} usernames...")
    start = datetime.now().timestamp()
    users = generate_usernames(mode, region, count)
    dur = datetime.now().timestamp() - start

    if not users:
        tg_send(chat_id, "❌ Gagal generate. Coba jumlah lebih kecil.")
        return

    content = "\n".join(users).encode("utf-8")
    fname = f"smth_{mode}_{region}_{len(users)}.txt"
    caption = (f"✅ <b>{len(users)}</b> usernames ({mode}/{region}) "
               f"dalam {dur:.1f}s")
    tg_send_doc(chat_id, fname, content, caption=caption)
    tg_send(chat_id, "Mau generate lagi?",
            kb([[
                {"text": "🔁 Lagi",  "callback_data": f"c:{mode}:{region}:{count}"},
                {"text": "🏠 Menu",  "callback_data": "menu:main"},
            ]]), html=True)

def handle_dup_start(chat_id):
    _PENDING[chat_id] = {"action": "dup_wait", "ts": datetime.now(timezone.utc).timestamp()}
    tg_send(chat_id,
            "<b>🔍 Check Dupes</b>\n\n"
            "Kirim file <b>.txt</b> atau <b>paste text</b> "
            "(satu entri per baris).",
            kb([[{"text": "⬅️ Batal", "callback_data": "menu:main"}]]),
            html=True)

def process_dup(chat_id, text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        tg_send(chat_id, "❌ Text kosong.")
        return
    counts = Counter(lines)
    dupes = {k: v for k, v in counts.items() if v > 1}
    extra = sum(v - 1 for v in dupes.values())
    msg = (f"<b>🔍 Hasil Cek Duplikat</b>\n\n"
           f"Total baris: <b>{len(lines)}</b>\n"
           f"Unik: <b>{len(counts)}</b>\n"
           f"Duplikat: <b>{len(dupes)}</b>\n"
           f"Extra entries: <b>{extra}</b>")
    if dupes:
        msg += "\n\n<b>Top duplikat:</b>\n"
        for k, v in sorted(dupes.items(), key=lambda x: -x[1])[:10]:
            esc = k.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            msg += f"• <code>{esc}</code> — {v}x\n"
    tg_send(chat_id, msg, kb([[{"text": "🏠 Menu", "callback_data": "menu:main"}]]),
            html=True)

def handle_split_start(chat_id):
    _PENDING[chat_id] = {"action": "split_wait", "ts": datetime.now(timezone.utc).timestamp()}
    tg_send(chat_id,
            "<b>✂️ Split File</b>\n\n"
            "Kirim file <b>.txt</b> yang mau di-split.",
            kb([[{"text": "⬅️ Batal", "callback_data": "menu:main"}]]),
            html=True)

def process_split_file(chat_id, file_id, filename):
    key = hashlib.md5(file_id.encode()).hexdigest()[:8]
    _PENDING[chat_id] = {"action": "split_chunk", "file_id": file_id,
                         "filename": filename, "key": key,
                         "ts": datetime.now(timezone.utc).timestamp()}
    tg_send(chat_id,
            f"📄 <b>{filename}</b>\n\nPilih <b>baris per file</b>:",
            kb_chunk(key), html=True)

def do_split(chat_id, file_id, base_name, chunk_size):
    tg_send(chat_id, "⏳ Downloading file...")
    # get file path from telegram
    r = tg_call("getFile", file_id=file_id)
    if not r.get("ok"):
        tg_send(chat_id, "❌ Gagal ambil file.")
        return
    file_path = r["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{TG_TOKEN}/{file_path}"
    try:
        content = requests.get(file_url, timeout=30).text
    except Exception as e:
        tg_send(chat_id, f"❌ Gagal download: {e}")
        return

    lines = content.splitlines(keepends=True)
    if not lines:
        tg_send(chat_id, "❌ File kosong.")
        return

    total = (len(lines) + chunk_size - 1) // chunk_size
    safe = "".join(c for c in base_name if c.isalnum() or c in "-_") or "split"
    safe = safe.replace(".txt", "")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        pad = max(3, len(str(total)))
        for i in range(total):
            chunk = lines[i * chunk_size:(i + 1) * chunk_size]
            name = f"{safe}_part_{i + 1:0{pad}d}.txt"
            zf.writestr(name, WATERMARK + "".join(chunk))
    buf.seek(0)

    files = {"document": (f"{safe}.zip", buf.read(), "application/zip")}
    data = {"chat_id": chat_id,
            "caption": f"✅ {len(lines)} baris → {total} file"}
    try:
        requests.post(f"{TG_API}/sendDocument", files=files, data=data, timeout=60)
        tg_send(chat_id, "Mau split lagi?",
                kb([[{"text": "🏠 Menu", "callback_data": "menu:main"}]]))
    except Exception as e:
        tg_send(chat_id, f"❌ Gagal kirim ZIP: {e}")

# ── main dispatcher ──

def process_update(update):
    _clean_pending()

    # callback query (tombol)
    if "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        msg_id = cb["message"]["message_id"]
        data = cb.get("data", "")
        tg_answer_cb(cb["id"])

        if data == "menu:main":
            tg_edit(chat_id, msg_id, "<b>SMTH Toolkit</b>\nPilih menu:", kb_main(), html=True)
            return
        if data == "menu:help":
            handle_help(chat_id)
            return
        if data == "menu:gen":
            handle_generate_flow(chat_id, msg_id)
            return
        if data == "menu:dup":
            handle_dup_start(chat_id)
            return
        if data == "menu:split":
            handle_split_start(chat_id)
            return

        # g:<mode> → region menu
        if data.startswith("g:"):
            mode = data[2:]
            tg_edit(chat_id, msg_id, f"<b>Mode: {mode}</b>\n\nPilih <b>region</b>:",
                    kb_regions(mode), html=True)
            return

        # r:<mode>:<region> → count menu
        if data.startswith("r:"):
            _, mode, region = data.split(":")
            tg_edit(chat_id, msg_id,
                    f"<b>{mode} / {region}</b>\n\nPilih <b>jumlah</b>:",
                    kb_counts(mode, region), html=True)
            return

        # c:<mode>:<region>:<count> → generate
        if data.startswith("c:"):
            _, mode, region, cnt = data.split(":")
            tg_edit(chat_id, msg_id, "⏳ Working...")
            do_generate(chat_id, mode, region, int(cnt))
            return

        # s:<key>:<chunk> → split
        if data.startswith("s:"):
            _, key, chunk = data.split(":")
            pending = _PENDING.get(chat_id)
            if not pending or pending.get("key") != key:
                tg_send(chat_id, "⚠️ Sesi expired. Kirim ulang file .txt.")
                return
            do_split(chat_id, pending["file_id"], pending["filename"], int(chunk))
            _PENDING.pop(chat_id, None)
            return
        return

    # message
    msg = update.get("message")
    if not msg:
        return
    chat_id = msg["chat"]["id"]
    user = msg.get("from", {})
    text = msg.get("text", "")
    doc = msg.get("document")

    if text.startswith("/start"):
        handle_start(chat_id, user); return
    if text.startswith("/help"):
        handle_help(chat_id); return
    if text.startswith("/generate"):
        handle_generate_flow(chat_id); return
    if text.startswith("/checkdup"):
        handle_dup_start(chat_id); return
    if text.startswith("/split"):
        handle_split_start(chat_id); return

    # document upload
    if doc:
        fname = doc.get("file_name", "file.txt")
        if not fname.lower().endswith(".txt"):
            tg_send(chat_id, "⚠️ Hanya file .txt yang didukung.")
            return
        pending = _PENDING.get(chat_id, {})
        action = pending.get("action")
        if action == "split_wait":
            process_split_file(chat_id, doc["file_id"], fname)
        elif action == "dup_wait":
            # download & process
            r = tg_call("getFile", file_id=doc["file_id"])
            if r.get("ok"):
                url = f"https://api.telegram.org/file/bot{TG_TOKEN}/{r['result']['file_path']}"
                try:
                    content = requests.get(url, timeout=30).text
                    _PENDING.pop(chat_id, None)
                    process_dup(chat_id, content)
                except Exception as e:
                    tg_send(chat_id, f"❌ {e}")
        else:
            tg_send(chat_id, "Pilih menu dulu ya. /start")
        return

    # plain text (potential dup check)
    pending = _PENDING.get(chat_id, {})
    if pending.get("action") == "dup_wait" and text:
        _PENDING.pop(chat_id, None)
        process_dup(chat_id, text)
        return

    # default
    tg_send(chat_id, "Ketik /start untuk menu.", kb_main())


@app.route(f'/api/telegram/{TG_SECRET}', methods=['POST'])
def telegram_webhook(TG_SECRET):
    if not TG_TOKEN:
        return jsonify({"error": "TELEGRAM_BOT_TOKEN not set"}), 500
    try:
        update = request.get_json(force=True, silent=True) or {}
        process_update(update)
    except Exception as e:
        print(f"webhook error: {e}")
    return "", 200


@app.route('/api/telegram/setup')
def telegram_setup():
    """Hit this once after deploy: /api/telegram/setup?url=https://your-app.vercel.app"""
    if not TG_TOKEN:
        return jsonify({"error": "TELEGRAM_BOT_TOKEN not set"}), 500
    base = request.args.get('url')
    if not base:
        return jsonify({"error": "pass ?url=https://your-app.vercel.app"}), 400
    webhook_url = f"{base.rstrip('/')}/api/telegram/{TG_SECRET}"
    r = requests.get(f"{TG_API}/setWebhook",
                     params={"url": webhook_url}, timeout=15).json()
    return jsonify({"webhook_url": webhook_url, "response": r})

application = app
