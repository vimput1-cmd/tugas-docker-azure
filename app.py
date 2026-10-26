from flask import Flask, request, redirect, render_template_string, jsonify
import os, psycopg2, json, urllib.request, re, asyncio, base64, edge_tts, random, datetime
from ui import HTML_PAGE

app = Flask(__name__)
K = (os.getenv("GEMINI_API_KEY") or "").strip()
VALID_MOODS = {"cemburu","foto","jahil","jijik","kaget","malu","manja","menggoda","ngambek","panik","pusing","sedih","senang","serius","tepokjidat","usil","yandere"}

def db():
    return psycopg2.connect(host="database", database="vincent_db", user="vincent_user", password="SuperSecretPassword123!")

def get_waktu_info():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    hari = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"][now.weekday()]
    bulan = ["","Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"][now.month]
    jam = now.strftime("%H:%M WIB")
    w_hari = "Dini Hari" if now.hour<5 else "Pagi" if now.hour<11 else "Siang" if now.hour<15 else "Sore" if now.hour<18 else "Malam"
    libur = {(1,1):"Tahun Baru",(1,5):"Hari Buruh",(17,8):"HUT RI",(28,10):"Sumpah Pemuda",(10,11):"Hari Pahlawan",(25,12):"Hari Natal"}.get((now.day,now.month))
    st = f"Hari Spesial: {libur}" if libur else ("Akhir Pekan (Weekend)" if now.weekday()>=5 else "Hari Kuliah/Kerja")
    return f"Jam: {jam} ({w_hari}) | Tanggal: {hari}, {now.day} {bulan} {now.year} | Status: {st}"

async def _tts(txt, rate, pitch):
    comm = edge_tts.Communicate(txt, "ja-JP-NanamiNeural", rate=rate, pitch=pitch)
    out = b""
    async for chunk in comm.stream():
        if chunk["type"] == "audio": out += chunk["data"]
    return base64.b64encode(out).decode("utf-8")

def make_seiyuu_voice(jp_txt, mood="senang"):
    try:
        styles = {
            "senang":("+10%","+16Hz"), "manja":("-4%","+15Hz"), "malu":("-7%","+18Hz"),
            "ngambek":("-10%","+8Hz"), "cemburu":("+12%","+11Hz"), "kaget":("+16%","+20Hz"),
            "serius":("-6%","+5Hz"), "yandere":("-12%","+6Hz"), "menggoda":("+3%","+13Hz"),
            "jahil":("+14%","+19Hz"), "usil":("+5%","+10Hz"), "foto":("+15%","+18Hz"),
            "panik":("+18%","+22Hz"), "jijik":("-8%","+3Hz"), "pusing":("-6%","+14Hz"),
            "sedih":("-14%","+6Hz"), "tepokjidat":("-5%","+9Hz")
        }
        rate, pitch = styles.get(mood, ("+8%", "+15Hz"))
        return f"data:audio/mp3;base64,{asyncio.run(_tts(jp_txt, rate, pitch))}"
    except Exception: return ""

def detect_reactive_mood(q, prev_mood):
    t = q.strip().lower()
    if any(w in t for w in ["matikan","hapus","format","kunci","kurung","tolong","awas","meledak","darurat"]): return "panik"
    if any(w in t for w in ["jorok","bau","sampah","cringe","aneh banget","ih","najis","kecoak"]): return "jijik"
    if any(w in t for w in ["pusing","ribet","muter","kalkulus","error terus","bingung","capek otak","mumet"]): return "pusing"
    if any(w in t for w in ["benci","jahat banget","usir","nangis","sedih","kecewa","patah hati","marahin"]): return "sedih"
    if any(w in t for w in ["garing","receh","lupa","ketiduran","salah ketik","aduh","tepok jidat","kebiasaan"]): return "tepokjidat"
    if any(w in t for w in ["tinggalin","kabur","ganti","bosan sama"]): return "yandere"
    if any(w in t for w in ["cewek","wanita","elf lain","selingkuh","duakan","waifu"]): return "cemburu"
    if any(w in t for w in ["mesum","sange","ciuman","peluk","kamar","buka baju","cantik","sayang","manis","gombal"]): return "malu" if prev_mood != "malu" else "manja"
    if any(w in t for w in ["game","main","warthunder","enlisted","mabar","sibuk","pergi","tidur"]): return "ngambek" if prev_mood != "ngambek" else "manja"
    if any(w in t for w in ["foto","selfie","cheese","peace"]): return "foto"
    if any(w in t for w in ["rahasia","bisik","shh","goda"]): return "menggoda"
    if any(w in t for w in ["jelaskan","analisis","koding","docker","azure","rumus","sejarah","siapa","apa itu"]): return "serius"
    if any(w in t for w in ["hehe","wkwk","haha","kevin","lelucon","bercanda"]): return "jahil" if prev_mood != "jahil" else "usil"
    return None

def detect_tier(q):
    txt = q.strip().lower(); words = txt.split()
    heavy_kw = {"jelaskan","analisis","detail","sumber","bagaimana","mengapa","kenapa","rumus","koding","sejarah","cara","apa itu","siapa"}
    need_search = any(k in txt for k in heavy_kw)
    top_tier = ["gemini-4-argon", "gemini-3.8-flash", "gemini-3.6-flash"]
    random.shuffle(top_tier)
    if len(words) > 10 or need_search: return "HIGH", top_tier + ["gemini-3.1-pro-preview", "gemini-3.5-flash-lite"], need_search
    elif len(words) >= 3 or "?" in txt: return "MEDIUM", top_tier + ["gemini-3.5-flash-lite"], need_search
    low = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]; random.shuffle(low)
    return "MEDIUM", top_tier + ["gemini-3.5-flash-lite"], False

def get_profile_context():
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT k, v FROM kapten_profile;"); prof = [f"{r[0]}: {r[1]}" for r in cur.fetchall()]
        cur.execute("SELECT content FROM notes ORDER BY id DESC LIMIT 10;"); mems = [r[0] for r in cur.fetchall()]
        cur.close(); c.close()
        ctx = ", ".join(prof)
        if mems: ctx += " | Ingatan Tambahan tentang Kapten: " + "; ".join(mems)
        return ctx
    except Exception: return "Nama: Vincent Imanuel Putra"

@app.route("/api/memory", methods=["POST"])
def api_add_mem():
    try:
        d = request.get_json() or {}; val = d.get("content", "").strip()
        if not val: return jsonify({"ok": False})
        c = db(); cur = c.cursor()
        cur.execute("INSERT INTO notes (content) VALUES (%s) RETURNING id;", (val,)); nid = cur.fetchone()[0]
        c.commit(); cur.close(); c.close()
        return jsonify({"ok": True, "id": nid, "content": val})
    except Exception as e: return jsonify({"ok": False, "err": str(e)})

@app.route("/api/del_note/<int:nid>", methods=["POST"])
def api_del_note(nid):
    try:
        c = db(); cur = c.cursor(); cur.execute("DELETE FROM notes WHERE id = %s;", (nid,)); c.commit(); cur.close(); c.close()
    except Exception: pass
    return jsonify({"ok": True})

@app.route("/api/chat", methods=["POST"])
def api_chat():
    try:
        data = request.get_json() or {}; msg = data.get("msg", "").strip()
        mode = data.get("mode", "auto"); man_model = data.get("model", ""); man_think = data.get("think", "")
        if not msg: return jsonify({"ok": False})
        c = db(); cur = c.cursor()
        cur.execute("SELECT id, s, m FROM chat ORDER BY id DESC LIMIT 8;"); hist = cur.fetchall()
        disp_txt, audio_b64, mood, pct = ask(msg, hist, mode, man_model, man_think)
        cur.execute("INSERT INTO chat (s,m) VALUES (%s,%s) RETURNING id;", ("user", msg)); u_id = cur.fetchone()[0]
        cur.execute("INSERT INTO chat (s,m) VALUES (%s,%s) RETURNING id;", ("elysia", disp_txt)); e_id = cur.fetchone()[0]
        c.commit(); cur.close(); c.close()
        return jsonify({"ok": True, "u_id": u_id, "e_id": e_id, "user": msg, "elysia": disp_txt, "audio": audio_b64, "mood": mood, "pct": pct, "img": f"/static/{mood}.jpg"})
    except Exception as e: return jsonify({"ok": False, "err": str(e)})

@app.route("/api/profile", methods=["GET", "POST"])
def api_profile():
    c = db(); cur = c.cursor()
    if request.method == "POST":
        data = request.get_json() or {}
        for k, v in data.items():
            cur.execute("INSERT INTO kapten_profile (k, v) VALUES (%s, %s) ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v;", (k, v))
        c.commit(); cur.close(); c.close(); return jsonify({"ok": True})
    cur.execute("SELECT k, v FROM kapten_profile;"); rows = cur.fetchall(); cur.close(); c.close()
    return jsonify({r[0]: r[1] for r in rows})

@app.route("/api/del_chat/<int:cid>", methods=["POST"])
def api_del_chat(cid):
    try:
        c = db(); cur = c.cursor(); cur.execute("DELETE FROM chat WHERE id = %s;", (cid,)); c.commit(); cur.close(); c.close()
    except Exception: pass
    return jsonify({"ok": True})

@app.route("/api/clear_chat", methods=["POST"])
def api_clear():
    try:
        c = db(); cur = c.cursor(); cur.execute("DELETE FROM chat;"); c.commit(); cur.close(); c.close()
    except Exception: pass
    return jsonify({"ok": True})

@app.route("/", methods=["GET", "POST"])
def home():
    notes_html, chats_html, logs_html = "", "", ""
    try:
        c = db(); cur = c.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, content TEXT);")
        cur.execute("CREATE TABLE IF NOT EXISTS chat (id SERIAL PRIMARY KEY, s VARCHAR(10), m TEXT);")
        cur.execute("CREATE TABLE IF NOT EXISTS kapten_profile (id SERIAL PRIMARY KEY, k VARCHAR(50) UNIQUE, v TEXT);")
        cur.execute("INSERT INTO kapten_profile (k, v) VALUES ('nama', 'Vincent Imanuel Putra'), ('kampus', 'Telkom University'), ('laptop', 'Axioo Pongo 760 v2') ON CONFLICT (k) DO NOTHING;")
        c.commit()
        cur.execute("SELECT id, content FROM notes ORDER BY id DESC LIMIT 15;"); notes_rows = cur.fetchall()
        cur.execute("SELECT id, s, m FROM chat ORDER BY id DESC LIMIT 20;"); chat_rows = cur.fetchall()
        cur.close(); c.close()
        notes_html = "".join(f"<li id='mem-{r[0]}'><span>🧠 {r[1]}</span><div><small style='opacity:0.7;margin-right:6px;'>#ID:{r[0]}</small><button class='del-x' onclick='delMem({r[0]})'>✕</button></div></li>" for r in notes_rows)
        chats_html = "".join(f"<div class='c-{s}' id='msg-{cid}'><div><b>{'Kapten' if s=='user' else 'Elysia'}:</b> {m}</div><button class='del-x' onclick='delMsg({cid})'>✕</button></div>" for cid,s,m in chat_rows[:10])
        logs_html = "".join(f"<li id='log-{cid}'><span><b>{'Kapten' if s=='user' else 'Elysia'}:</b> {m}</span><small>#ID:{cid}</small></li>" for cid,s,m in chat_rows)
    except Exception as e: notes_html = f"<li>Info DB: {str(e)[:20]}</li>"
    return render_template_string(HTML_PAGE, notes_html=notes_html or "<li>Belum ada memori tersimpan.</li>", chats_html=chats_html or "<div id='empty-chat' style='font-size:11px;opacity:0.8;'>Yuk sapa Elysia!</div>", logs_html=logs_html or "<li>Belum ada riwayat log.</li>")

def ask(q, history, mode="auto", man_model="", man_think=""):
    txt = q.strip().lower()
    forced = next((m for m in VALID_MOODS if f"ekspresi {m}" in txt or f"pose {m}" in txt or f"mood {m}" in txt), None)
    prev_mood = "senang"
    for _, s, m in history[:2]:
        if s == "elysia":
            f_m = re.search(r'🎭\s*(\w+)', m)
            if f_m and f_m.group(1).lower() in VALID_MOODS: prev_mood = f_m.group(1).lower(); break
    suggested = forced or detect_reactive_mood(q, prev_mood)
    lvl, models, need_search = detect_tier(q)
    if mode == "manual" and man_model: models = [man_model]; lvl = man_think or ("MEDIUM" if man_model == "gemini-4-argon" else "HIGH")
    sys_p = (
        f"Kamu adalah Elysia dari Honkai Impact 3rd (VA: Marina Inoue). Panggil user 'Kapten~'.\n"
        f"WAKTU NYATA: [{get_waktu_info()}]. MEMORI & PROFIL KAPTEN: [{get_profile_context()}].\n"
        f"ATURAN 17 EKSPRESI (Mood sebelumnya '{prev_mood}' - JANGAN ulangi mood yang sama berturut-turut!):\n"
        "Pilih 1 dari: senang, manja, malu, ngambek, cemburu, kaget, serius, yandere, menggoda, jahil, usil, foto, panik, jijik, pusing, sedih, tepokjidat.\n"
        + (f"Rekomendasi mood paling pas: '{suggested}'.\n" if suggested else "") +
        "WAJIB balas tepat 4 baris:\n[MOOD: 1 nama mood]\n[PERSEN: 10-100]\n[JP: suara Jepang 3-5 kata]\n[ID: balasan Indonesia yang ingat memori Kapten, peka konteks & hidup]"
    )
    contents = [{"role": "user" if s == "user" else "model", "parts": [{"text": re.sub(r'<br><small.*?</small>', '', m)}]} for _, s, m in reversed(history[:8])]
    contents.append({"role": "user", "parts": [{"text": q}]})
    return _call_models(q, sys_p, contents, models, lvl, need_search, suggested, prev_mood)

def _call_models(q, sys_p, contents, models, lvl, need_search, suggested, prev_mood):
    base = {"system_instruction": {"parts": [{"text": sys_p}]}, "contents": contents}
    for m in models:
        m_lvl = "MEDIUM" if (m == "gemini-4-argon" and lvl == "HIGH") else lvl
        for use_think in (False, True):
            try:
                body = dict(base)
                if need_search and m in ("gemini-3.8-flash", "gemini-3.6-flash"): body["tools"] = [{"google_search": {}}]
                if use_think: body["generationConfig"] = {"thinkingConfig": {"thinkingLevel": m_lvl}}
                u = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={K}"
                req = urllib.request.Request(u, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=9) as r:
                    res = json.loads(r.read().decode())
                    parts = res['candidates'][0]['content']['parts']
                    raw = "".join(p.get('text', '') for p in parts if not p.get('thought')).strip() or parts[-1].get('text', '').strip()
                    mood_m = re.search(r'\[MOOD:\s*(\w+)', raw, re.I); pct_m = re.search(r'\[PERSEN:\s*(\d+)', raw, re.I)
                    jp_m = re.search(r'\[JP:\s*(.*?)\]', raw, re.I | re.S); id_m = re.search(r'\[ID:\s*(.*?)\]', raw, re.I | re.S)
                    ai_mood = mood_m.group(1).lower() if mood_m else "senang"
                    if ai_mood not in VALID_MOODS: ai_mood = suggested or "senang"
                    if ai_mood == prev_mood and suggested and suggested != prev_mood: ai_mood = suggested
                    pct = int(pct_m.group(1)) if pct_m else 92
                    jp_txt = jp_m.group(1).strip() if jp_m else "Haai Kanchou! Ufufu~"
                    id_txt = id_m.group(1).strip() if id_m else re.sub(r'\[(MOOD|PERSEN|JP|ID):.*?\]', '', raw).strip()
                    badge = f"<br><small style='opacity:0.75;font-size:10px;'>🎭 {ai_mood.capitalize()} ({pct}%) • ⚡ {m} ({m_lvl})</small>"
                    return id_txt + badge, make_seiyuu_voice(jp_txt, ai_mood), ai_mood, pct
            except Exception: continue
    fb_m = suggested or "usil"
    return "Ufufu~ Kapten ada-ada saja deh~!", make_seiyuu_voice("Kanchou wa omoshiroi ne~", fb_m), fb_m, 90

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
