import os
import sys
import io
import zipfile
import random
import string
import json
from datetime import datetime
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory, send_file

app = Flask(__name__, static_folder='../public', static_url_path='')

# ==========================================
#               SMTH TOOLKIT V2
#              PROPERTY OF SMTH
#                  SMTH©2026
# ==========================================

VERSION = "2.5"

WATERMARK = (
    "========================================\n"
    "               SMTH©2026\n"
    "            PROPERTY OF SMTH\n"
    "========================================\n\n"
)

# ── DATABASE KATA (Fallback) ──
FALLBACK_WORDS = [
    "alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel",
    "india", "juliet", "kilo", "lima", "mike", "november", "oscar", "papa",
    "quebec", "romeo", "sierra", "tango", "uniform", "victor", "whiskey",
    "xray", "yankee", "zulu", "aria", "bima", "citra", "dewi", "eka",
    "fajar", "gita", "hadi", "indah", "joko", "kartika", "lina", "maya",
    "nanda", "oscar", "putri", "raka", "sari", "tio", "uma", "vino",
    "wati", "yudi", "zahra", "nabil", "rafi", "zaki", "nadia", "dian"
]

def get_word_pool():
    """Ambil database kata. Kalau nggak ada, pake fallback."""
    db_path = os.path.join(os.path.dirname(__file__), "words_database.txt")
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            words = [w.strip() for w in f.readlines() if 3 <= len(w.strip()) <= 15]
        if words:
            return words
    return FALLBACK_WORDS

# ── ENDPOINT: GENERATE USERNAMES ──
@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        mode = data.get('mode', 'plain')
        region = data.get('region', 'indonesia')
        name_length = data.get('nameLength', 'both')
        count = int(data.get('count', 10))

        if count <= 0 or count > 1000000:
            return jsonify({"status": "error", "msg": "Jumlah harus 1-10000"})

        pool_words = get_word_pool()

        if region == "indonesia":
            pool_words = [w for w in pool_words if len(w) >= 3]

        if name_length == "long":
            pool_words = [w for w in pool_words if len(w) >= 8]
        elif name_length == "short":
            pool_words = [w for w in pool_words if len(w) <= 7]

        if not pool_words:
            pool_words = FALLBACK_WORDS

        generated = set()
        attempts = 0
        max_attempts = count * 20

        while len(generated) < count and attempts < max_attempts:
            attempts += 1
            base = random.choice(pool_words)
            base = ''.join(e for e in base if e.isalnum() and e.isascii())
            if not base:
                continue
            base = base.capitalize()

            if mode == "plain":
                username = base
            elif mode == "2digit":
                username = f"{base}{random.randint(10, 99)}"
            elif mode == "3digit":
                username = f"{base}{random.randint(100, 999)}"
            elif mode == "4digit":
                username = f"{base}{random.randint(1000, 9999)}"
            elif mode == "mix":
                choice = random.choice(["plain", "2digit", "3digit", "4digit"])
                if choice == "plain":
                    username = base
                elif choice == "2digit":
                    username = f"{base}{random.randint(10, 99)}"
                elif choice == "3digit":
                    username = f"{base}{random.randint(100, 999)}"
                else:
                    username = f"{base}{random.randint(1000, 9999)}"
            else:
                username = base

            if len(username) < 6:
                while len(username) < 6:
                    username += random.choice(string.ascii_lowercase + string.digits)
            elif len(username) > 20:
                username = username[:20]

            if 6 <= len(username) <= 20:
                generated.add(f"{username}:{username}")

        result = list(generated)
        random.shuffle(result)

        return jsonify({
            "status": "success",
            "total": len(result),
            "data": result
        })

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


# ── ENDPOINT: DUPLICATE CHECKER ──
@app.route('/api/check-duplicates', methods=['POST'])
def check_duplicates():
    try:
        data = request.json
        text_content = data.get('text', '')
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]

        counts = Counter(lines)
        duplicates = {item: count for item, count in counts.items() if count > 1}
        total_duplicate_entries = sum(count - 1 for count in duplicates.values())

        return jsonify({
            "status": "success",
            "total_lines": len(lines),
            "unique": len(counts),
            "dupes": len(duplicates),
            "extra": total_duplicate_entries,
            "duplicate_list": [{"item": k, "count": v} for k, v in duplicates.items()]
        })
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


# ── ENDPOINT: SPLIT FILE → ZIP ──
@app.route('/api/split', methods=['POST'])
def split_file():
    try:
        data = request.json
        text_content = data.get('text', '')
        chunk_size = int(data.get('chunkSize', 100))
        base_name = (data.get('filename') or 'split_result').strip()

        if chunk_size <= 0:
            return jsonify({"status": "error", "msg": "Chunk size harus > 0"})

        lines = text_content.splitlines(keepends=True)
        if not lines:
            return jsonify({"status": "error", "msg": "File kosong!"})

        total_parts = (len(lines) + chunk_size - 1) // chunk_size

        # Sanitize nama file dasar (biar aman buat ZIP & filesystem)
        safe_name = "".join(
            c for c in base_name if c.isalnum() or c in "-_"
        ) or "split_result"

        # Bangun ZIP di memory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            # pad numbering biar sortable
            pad = max(3, len(str(total_parts)))
            for index in range(total_parts):
                start = index * chunk_size
                end = start + chunk_size
                chunk = lines[start:end]
                part_name = f"{safe_name}_part_{index + 1:0{pad}d}.txt"
                content = WATERMARK + "".join(chunk)
                zf.writestr(part_name, content)
        buf.seek(0)

        resp = send_file(
            buf,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{safe_name}.zip"
        )
        # metadata buat UI
        resp.headers['X-Total-Lines'] = str(len(lines))
        resp.headers['X-Total-Files'] = str(total_parts)
        resp.headers['X-Zip-Name'] = f"{safe_name}.zip"
        return resp

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


# ── ROUTE UNTUK SERVE HTML ──
@app.route('/')
def index():
    return send_from_directory('../public', 'index.html')


# ── VERCEL HANDLER ──
def handler(request):
    return app(request.environ, request.start_response)
