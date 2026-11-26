import os
import io
import zipfile
import random
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory, send_file

app = Flask(__name__, static_folder='../public', static_url_path='')

# ==========================================
#               SMTH TOOLKIT V2.6
#              PROPERTY OF SMTH
#                  SMTH©2026
# ==========================================

VERSION = "2.6"

WATERMARK = (
    "========================================\n"
    "               SMTH©2026\n"
    "            PROPERTY OF SMTH\n"
    "========================================\n\n"
)

# ==========================================================
#   WORD POOLS — nama asli per region (lowercase)
#   Tambah/kurangi sesuai kebutuhan. Bisa juga taruh file
#   words_database.txt di folder yang sama (satu kata per baris).
# ==========================================================
_RAW_POOLS = {
    "indonesia": [
        "adi", "agung", "agus", "ahmad", "aisyah", "aldi", "alif", "amelia",
        "andi", "andra", "angga", "anggun", "ani", "anisa", "anwar", "ardi",
        "ari", "arif", "aris", "arman", "asep", "ayu", "bagas", "bagus",
        "bayu", "bella", "beni", "bima", "budi", "cahaya", "candra", "citra",
        "damar", "dara", "dedi", "dewi", "dian", "dina", "dinda", "dodi",
        "doni", "dwi", "eka", "eko", "endang", "erik", "erna", "fahmi",
        "fajar", "farhan", "farida", "fauzi", "febri", "feri", "fitri",
        "galih", "gita", "gunawan", "hadi", "hana", "haris", "hendra",
        "hesti", "hilmi", "indah", "indra", "intan", "iqbal", "irfan",
        "irma", "ivan", "iwan", "jaka", "jihan", "joko", "kamila",
        "kartika", "kiki", "kurnia", "lina", "linda", "lisa", "lukman",
        "lutfi", "maya", "mega", "miko", "mila", "mita", "nabila", "nanda",
        "naufal", "nia", "nisa", "novi", "nurul", "pandu", "putra", "putri",
        "rafi", "rahmat", "raihan", "raka", "rama", "rani", "ratna", "rendi",
        "reza", "rifki", "rina", "rizki", "roni", "rosita", "rudi", "saiful",
        "salsabila", "sandi", "santoso", "sari", "satria", "sinta", "siti",
        "sofia", "sri", "sugeng", "sukma", "surya", "syifa", "tania",
        "taufik", "teguh", "tiara", "tika", "tri", "wahyu", "wati", "wendi",
        "widya", "wijaya", "wulan", "yani", "yanto", "yasin", "yoga",
        "yudi", "yuliana", "yusuf", "zahra", "zaki", "zainal", "zulfa",
    ],
    "philippines": [
        "andrea", "angela", "angelo", "anna", "anthony", "bea", "ben",
        "bianca", "carlo", "carmela", "celine", "charles", "cheryl", "chris",
        "christian", "christine", "clarisse", "daniel", "david", "dennis",
        "diana", "diane", "dominic", "donna", "edgar", "eduardo", "ella",
        "emilio", "emmanuel", "eric", "erica", "faith", "fernando", "francis",
        "gabriel", "gemma", "grace", "hannah", "hazel", "heart", "ian",
        "isabel", "ivan", "james", "janine", "jasmine", "jay", "jayson",
        "jenny", "jerome", "jessa", "jessica", "jhon", "joel", "john",
        "jomar", "jose", "joseph", "joshua", "joy", "juan", "julia",
        "karen", "karla", "kate", "kevin", "kim", "kristine", "kurt",
        "kyle", "lara", "larry", "lawrence", "leah", "leo", "liza",
        "lorenz", "louise", "lucas", "mae", "marco", "maria", "marie",
        "mark", "marlon", "mary", "michael", "michelle", "miguel", "mika",
        "nancy", "natalie", "nicole", "nikki", "noel", "paolo", "patricia",
        "paul", "paula", "peter", "princess", "rachel", "rafael", "ralph",
        "ramon", "renz", "rex", "rica", "richard", "robert", "rodel",
        "roger", "rose", "rowena", "ryan", "sam", "sarah", "shane",
        "sophia", "stephanie", "trisha", "vanessa", "vince", "vincent",
        "yna", "zara",
    ],
    "malaysia": [
        "ahmad", "aidil", "aiman", "aina", "aisyah", "akmal", "alia",
        "amalina", "amir", "amira", "anis", "anisah", "anwar", "aqil",
        "aqilah", "arif", "ariff", "azlan", "azman", "azmi", "bakar",
        "balqis", "danial", "danish", "dhabitah", "faiz", "faizal", "farah",
        "farid", "faris", "fatimah", "fatin", "hafiz", "hakim", "hakimi",
        "halim", "hamzah", "hana", "hanis", "haris", "hassan", "hazim",
        "hazwan", "hidayah", "huda", "ilyas", "iman", "imran", "irfan",
        "iskandar", "ismail", "izzati", "johari", "kamal", "kamarul",
        "kartini", "khairul", "laila", "latifah", "liyana", "luqman",
        "mahathir", "maisarah", "maisara", "malik", "mazlan", "megat",
        "mohd", "murni", "nabila", "nadia", "naim", "nazira", "nazmi",
        "nik", "noor", "nora", "nur", "nuraina", "omar", "osman",
        "qistina", "rafiq", "rahim", "rahman", "raihana", "ramli", "rashid",
        "razak", "ridzuan", "rizal", "roslan", "rosli", "sabrina",
        "saiful", "salleh", "samad", "sarah", "shafiq", "shah", "shukri",
        "sofea", "sulaiman", "syafiq", "syahmi", "syazwan", "tan", "tengku",
        "wan", "yaakob", "yasmin", "yusof", "zahid", "zaidi", "zainal",
        "zakaria", "zarith", "zikri", "zul", "zulaikha", "zulkifli",
    ],
    "singapore": [
        "aaron", "adeline", "aisyah", "alex", "alvin", "amanda", "amber",
        "andrew", "angela", "arjun", "ben", "benjamin", "brandon", "bryan",
        "charmaine", "cheryl", "chloe", "chris", "christina", "chua",
        "claire", "darren", "david", "deepa", "denise", "derek", "devi",
        "diana", "edwin", "elaine", "eric", "eugene", "faizal", "fiona",
        "foo", "gabriel", "gerald", "goh", "gopal", "grace", "hafiz",
        "hakim", "hazel", "hui", "ismail", "ivan", "james", "jasmine",
        "jaya", "jie", "joel", "jonathan", "jovan", "jun", "justin",
        "karen", "kavitha", "kelvin", "kenneth", "kevin", "kimberly",
        "koh", "krishna", "kumar", "lakshmi", "larry", "latha", "lee",
        "leonard", "lex", "lim", "ling", "lionel", "marcus", "mei",
        "melissa", "ming", "mohan", "nair", "nancy", "natalie", "ng",
        "nigel", "nisha", "ong", "pillai", "priya", "rachel", "raj",
        "ramesh", "ravi", "rebecca", "ryan", "samuel", "sarah", "sean",
        "sen", "sheryl", "siva", "sophia", "stephanie", "suresh", "surya",
        "tan", "tay", "teo", "timothy", "vanessa", "vijay", "vincent",
        "vivian", "wei", "wong", "xin", "yan", "yeo", "yi", "zhi", "zoe",
    ],
}


def _clean_word(w):
    """Buang karakter non-alnum non-ascii, lowercase."""
    w = ''.join(ch for ch in str(w).strip() if ch.isalnum() and ch.isascii())
    return w.lower()


def _dedup(seq):
    seen, out = set(), []
    for w in seq:
        cw = _clean_word(w)
        if cw and cw not in seen:
            seen.add(cw)
            out.append(cw)
    return out


WORD_POOLS = {k: _dedup(v) for k, v in _RAW_POOLS.items()}
WORD_POOLS["global"] = _dedup([w for v in _RAW_POOLS.values() for w in v])

# ==========================================================
#   External database (opsional): words_database.txt
#   Di-cache berbasis mtime — tidak dibaca ulang tiap request.
# ==========================================================
_EXTERNAL_CACHE = {"mtime": None, "words": []}


def load_external_words():
    db_path = os.path.join(os.path.dirname(__file__), "words_database.txt")
    if not os.path.exists(db_path):
        return []
    try:
        mtime = os.path.getmtime(db_path)
    except OSError:
        return []
    if _EXTERNAL_CACHE["mtime"] == mtime:
        return _EXTERNAL_CACHE["words"]
    try:
        words = []
        with open(db_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                words.append(line)
        cleaned = _dedup(words)
        _EXTERNAL_CACHE["mtime"] = mtime
        _EXTERNAL_CACHE["words"] = cleaned
        return cleaned
    except Exception:
        return []


def get_word_pool(region):
    region = (region or "indonesia").lower()
    base = WORD_POOLS.get(region) or WORD_POOLS["global"]
    return _dedup(list(base) + load_external_words())


# mode -> (max_digits, digit_span, digit_base)
DIGIT_INFO = {
    "plain":  (0, 1,   0),
    "2digit": (2, 90,  10),
    "3digit": (3, 900, 100),
    "4digit": (4, 9000, 1000),
    "mix":    (4, 9991, None),   # 1 + 90 + 900 + 9000
}


def capacity_of(mode, pool_size):
    if mode not in DIGIT_INFO:
        return pool_size
    return pool_size * DIGIT_INFO[mode][1]


def prepare_pool(pool, mode, name_length, min_len, max_len):
    """Filter pool supaya semua kombinasi (word + digit) pas di [min_len, max_len]."""
    # filter name length dulu
    if name_length == "short":
        pool = [w for w in pool if len(w) <= 7]
    elif name_length == "long":
        pool = [w for w in pool if len(w) >= 8]

    if mode == "plain":
        lo, hi = min_len, max_len
    elif mode in ("2digit", "3digit", "4digit"):
        d = DIGIT_INFO[mode][0]
        lo, hi = max(3, min_len - d), max_len - d
    elif mode == "mix":
        lo, hi = max(3, min_len), max_len - 4
    else:
        lo, hi = min_len, max_len

    if hi < lo:
        return []
    return [w for w in pool if lo <= len(w) <= hi]


def generate_combos(pool, mode, count, min_len, max_len):
    """Sampling unik O(count) — tanpa retry loop, tanpa duplikat."""
    rng = random.SystemRandom()
    pool_size = len(pool)
    if pool_size == 0 or count <= 0:
        return []

    if mode == "plain":
        count = min(count, pool_size)
        picked = rng.sample(pool, count)
        return [f"{w}:{w}" for w in picked]

    if mode in ("2digit", "3digit", "4digit"):
        d, span, base = DIGIT_INFO[mode]
        cap = pool_size * span
        count = min(count, cap)
        idxs = rng.sample(range(cap), count)
        out = []
        for i in idxs:
            w = pool[i // span]
            num = base + (i % span)
            uname = f"{w}{num}"
            if min_len <= len(uname) <= max_len:
                out.append(f"{uname}:{uname}")
        return out

    if mode == "mix":
        SUB = 9991
        cap = pool_size * SUB
        count = min(count, cap)
        idxs = rng.sample(range(cap), count)
        out = []
        for i in idxs:
            w = pool[i // SUB]
            sub = i % SUB
            # sub=0 -> plain; sub=1..90 -> 10..99; 91..990 -> 100..999; 991..9990 -> 1000..9999
            uname = w if sub == 0 else f"{w}{sub + 9}"
            if min_len <= len(uname) <= max_len:
                out.append(f"{uname}:{uname}")
        return out

    return [f"{w}:{w}" for w in pool[:count]]


# ── ENDPOINT: GENERATE ──
@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json(silent=True) or {}
        mode = (data.get('mode') or 'plain').lower()
        region = (data.get('region') or 'indonesia').lower()
        name_length = (data.get('nameLength') or 'both').lower()
        count = int(data.get('count', 10))
        min_len = int(data.get('minLength', 3))
        max_len = int(data.get('maxLength', 20))

        if mode not in DIGIT_INFO:
            return jsonify({"status": "error", "msg": f"Mode tidak dikenal: {mode}"})
        if count < 1 or count > 15000:
            return jsonify({"status": "error", "msg": "Jumlah harus 1-15000"})
        if min_len < 3:
            min_len = 3
        if max_len > 24:
            max_len = 24
        if min_len > max_len:
            min_len, max_len = max_len, min_len

        raw_pool = get_word_pool(region)
        pool = prepare_pool(raw_pool, mode, name_length, min_len, max_len)

        if not pool:
            return jsonify({
                "status": "error",
                "msg": (f"Pool kata kosong untuk region '{region}' mode '{mode}' "
                        f"dengan filter name length '{name_length}'. "
                        f"Coba region lain, mode lain, atau longgarkan filter.")
            })

        cap = capacity_of(mode, len(pool))
        if count > cap:
            return jsonify({
                "status": "error",
                "msg": (f"Mode '{mode}' untuk region '{region}' hanya sanggup "
                        f"{cap:,} combo unik (pool {len(pool)} kata). "
                        f"Kurangi count atau gunakan mode dengan digit lebih banyak.")
            })

        result = generate_combos(pool, mode, count, min_len, max_len)
        random.shuffle(result)

        return jsonify({
            "status": "success",
            "total": len(result),
            "pool_size": len(pool),
            "capacity": cap,
            "mode": mode,
            "region": region,
            "data": result,
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
            "duplicate_list": [{"item": k, "count": v} for k, v in duplicates.items()],
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

        safe_name = "".join(c for c in base_name if c.isalnum() or c in "-_") or "split_result"

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            pad = max(3, len(str(total_parts)))
            for index in range(total_parts):
                start = index * chunk_size
                end = start + chunk_size
                chunk = lines[start:end]
                part_name = f"{safe_name}_part_{index + 1:0{pad}d}.txt"
                zf.writestr(part_name, WATERMARK + "".join(chunk))
        buf.seek(0)

        resp = send_file(
            buf, mimetype='application/zip', as_attachment=True,
            download_name=f"{safe_name}.zip"
        )
        resp.headers['X-Total-Lines'] = str(len(lines))
        resp.headers['X-Total-Files'] = str(total_parts)
        resp.headers['X-Zip-Name'] = f"{safe_name}.zip"
        return resp

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@app.route('/')
def index():
    return send_from_directory('../public', 'index.html')


# Vercel Python runtime otomatis mendeteksi variabel `app` (Flask WSGI).
# Tidak perlu handler() manual lagi.
