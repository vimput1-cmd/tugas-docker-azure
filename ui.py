PART_STYLE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Elysia CloudApp VN</title><style>
body{margin:0;font-family:'Segoe UI',sans-serif;color:#fff;min-height:100vh;display:flex;justify-content:space-between;align-items:flex-end;padding:20px 2.5vw;box-sizing:border-box;overflow:hidden;background:#000;}
.vn-stage{position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-2;overflow:hidden;}
.vn-sprite{width:100vw;height:100vh;object-fit:cover;object-position:center 20%;transition:opacity 0.22s ease-in-out;}
.ov{position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(180deg,rgba(0,0,0,0.0) 65%,rgba(10,15,25,0.45) 100%);z-index:-1;pointer-events:none;}
.hud{position:fixed;top:18px;left:2.5vw;background:rgba(15,23,42,0.68);backdrop-filter:blur(16px);padding:12px 16px;border-radius:15px;border:1px solid rgba(255,255,255,0.3);width:250px;}
.bar-bg{width:100%;height:8px;background:rgba(255,255,255,0.2);border-radius:6px;overflow:hidden;margin-top:6px;}
.bar-fill{height:100%;width:90%;background:linear-gradient(90deg,#ff758c,#ff7eb3);transition:width 0.4s ease;}
.card{background:rgba(15,23,42,0.66);backdrop-filter:blur(16px);padding:15px;border-radius:16px;width:370px;box-shadow:0 8px 30px rgba(0,0,0,0.55);border:1px solid rgba(255,255,255,0.28);}
.ctrl-bar{display:flex;gap:5px;margin:6px 0 8px 0;font-size:11px;flex-wrap:wrap;}
.ctrl-bar select,.tab-btn{background:rgba(255,255,255,0.18);color:#fff;border:1px solid rgba(255,255,255,0.28);border-radius:6px;padding:3px 8px;font-size:11px;outline:none;cursor:pointer;}
.tab-btn.active{background:linear-gradient(135deg,#ff758c,#ff7eb3);border-color:transparent;font-weight:600;}
.ctrl-bar select option{background:#0f172a;color:#fff;}
.row-in{display:flex;gap:6px;margin-bottom:6px;} input{flex:1;padding:8px 10px;border-radius:8px;border:none;outline:none;background:rgba(255,255,255,0.92);color:#111;font-size:13px;}
button.btn-send{padding:8px 14px;border-radius:8px;border:none;background:linear-gradient(135deg,#ff758c,#ff7eb3);color:#fff;font-weight:600;cursor:pointer;font-size:13px;}
.chat-box{max-height:140px;overflow-y:auto;display:flex;flex-direction:column-reverse;margin-bottom:8px;}
.c-user,.c-elysia,ul.mem-list li{margin:4px 0;padding:6px 10px;border-radius:8px;font-size:12px;display:flex;justify-content:space-between;align-items:center;gap:6px;line-height:1.4;}
.c-user{background:rgba(255,255,255,0.22);align-self:flex-end;} .c-elysia{background:rgba(255,117,140,0.5);align-self:flex-start;}
ul.mem-list{list-style:none;padding:0;margin:0;max-height:125px;overflow-y:auto;}
ul.mem-list li{background:rgba(255,255,255,0.16);border:1px solid rgba(255,255,255,0.15);}
.del-x{background:transparent;border:none;color:rgba(255,255,255,0.65);padding:0 3px;font-size:11px;cursor:pointer;}
.modal{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#0f172a;border:1px solid rgba(255,255,255,0.3);border-radius:16px;padding:20px;width:320px;z-index:99;display:none;box-shadow:0 10px 40px rgba(0,0,0,0.8);}
.modal input{width:100%;margin-bottom:8px;padding:6px;border-radius:6px;border:none;box-sizing:border-box;}
</style></head><body>"""

PART_BODY = """
<div class="vn-stage"><img id="vn-img" class="vn-sprite" src="/static/senang.jpg" alt="Elysia"></div>
<canvas id="wind-cvs" style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;"></canvas>
<div class="ov"></div>
<div class="hud"><div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;"><span id="m-label">Mood: Senang</span><span id="m-pct">90%</span></div><div class="bar-bg"><div id="m-bar" class="bar-fill"></div></div></div>
<div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <h3 style="margin:0;font-size:17px;">Elysia AI Chat</h3>
        <div>
            <button type="button" onclick="openProfile()" style="background:rgba(255,255,255,0.2);border:none;color:#fff;padding:3px 7px;font-size:11px;border-radius:6px;cursor:pointer;">👤 Profil</button>
            <button type="button" onclick="clearChat()" style="background:rgba(255,75,100,0.3);border:none;color:#fff;padding:3px 7px;font-size:11px;border-radius:6px;cursor:pointer;">Hapus Semua</button>
        </div>
    </div>
    <div class="ctrl-bar">
        <select id="cmode" onchange="toggleMode()">
            <option value="auto">⚡ Otomatis (4-Argon/3.8/3.6 • Med-High)</option>
            <option value="manual">🛠️ Manual (Pilih Model & Level)</option>
        </select>
        <span id="m-ctrl" style="display:none;gap:4px;">
            <select id="cmodel"><option value="gemini-4-argon">4-Argon</option><option value="gemini-3.8-flash">3.8-Flash</option><option value="gemini-3.6-flash">3.6-Flash</option><option value="gemini-3.5-flash-lite">3.5-Lite</option><option value="gemini-3.1-pro-preview">3.1-Pro</option></select>
            <select id="cthink"><option value="HIGH">High</option><option value="MEDIUM">Medium</option><option value="LOW">Low</option></select>
        </span>
    </div>
    <div class="chat-box" id="cbox">{{ chats_html|safe }}</div>
    <form onsubmit="sendChat(event)"><div class="row-in"><input id="cinput" placeholder="Ajak Elysia bicara..." required autocomplete="off"><button type="submit" class="btn-send" id="cbtn">Kirim</button></div></form>
</div>
<div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
        <h3 style="margin:0;font-size:17px;">Elysia Memory Vault</h3>
        <div style="display:flex;gap:4px;">
            <button type="button" id="tb-mem" class="tab-btn active" onclick="swTab('mem')">🧠 Memori</button>
            <button type="button" id="tb-log" class="tab-btn" onclick="swTab('log')">📜 Riwayat</button>
        </div>
    </div>
    <p style="margin:0 0 8px 0;font-size:11px;opacity:0.85;">Azure VM (70.153.140.113) • PostgreSQL Memory DB</p>
    <div id="pane-mem">
        <form onsubmit="addMem(event)"><div class="row-in"><input id="minput" placeholder="Tanamkan ingatan baru ke Elysia..." required autocomplete="off"><button type="submit" class="btn-send">Simpan</button></div></form>
        <ul class="mem-list" id="mlist">{{ notes_html|safe }}</ul>
    </div>
    <div id="pane-log" style="display:none;">
        <ul class="mem-list" id="llist">{{ logs_html|safe }}</ul>
    </div>
</div>
<div id="prof-modal" class="modal">
    <h4 style="margin:0 0 10px 0;">👤 Profil Pribadi Kapten</h4>
    <small style="opacity:0.8;">Nama / Panggilan:</small><input id="p-nama">
    <small style="opacity:0.8;">Kampus / Jurusan:</small><input id="p-kampus">
    <small style="opacity:0.8;">Laptop / Hobi:</small><input id="p-laptop">
    <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:10px;">
        <button onclick="closeProfile()" style="background:#555;border:none;color:#fff;padding:6px 12px;border-radius:6px;cursor:pointer;">Batal</button>
        <button onclick="saveProfile()" style="background:#ff758c;border:none;color:#fff;padding:6px 14px;border-radius:6px;cursor:pointer;font-weight:600;">Simpan</button>
    </div>
</div>"""

PART_JS1 = """
<script>
let curAudio = null;
["cemburu","foto","jahil","jijik","kaget","malu","manja","menggoda","ngambek","panik","pusing","sedih","senang","serius","tepokjidat","usil","yandere"].forEach(m => { const i = new Image(); i.src = `/static/${m}.jpg`; });
function toggleMode(){ document.getElementById('m-ctrl').style.display = (document.getElementById('cmode').value === 'manual') ? 'inline-flex' : 'none'; }
function swTab(t){
    document.getElementById('pane-mem').style.display = (t==='mem') ? 'block' : 'none';
    document.getElementById('pane-log').style.display = (t==='log') ? 'block' : 'none';
    document.getElementById('tb-mem').classList.toggle('active', t==='mem');
    document.getElementById('tb-log').classList.toggle('active', t==='log');
}
async function addMem(e){
    e.preventDefault();
    const inp = document.getElementById('minput'), val = inp.value.trim(); if(!val) return;
    inp.value = '';
    const res = await fetch('/api/memory', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({content:val})});
    const d = await res.json();
    if(d.ok){
        document.getElementById('mlist').insertAdjacentHTML('afterbegin', `<li id='mem-${d.id}'><span>🧠 ${d.content}</span><div><small style='opacity:0.7;margin-right:6px;'>#ID:${d.id}</small><button class='del-x' onclick='delMem(${d.id})'>✕</button></div></li>`);
    }
}
async function delMem(id){ await fetch('/api/del_note/' + id, {method:'POST'}); const el = document.getElementById('mem-' + id); if(el) el.remove(); }
async function openProfile(){
    const res = await fetch('/api/profile'); const d = await res.json();
    document.getElementById('p-nama').value = d.nama || ''; document.getElementById('p-kampus').value = d.kampus || ''; document.getElementById('p-laptop').value = d.laptop || '';
    document.getElementById('prof-modal').style.display = 'block';
}
function closeProfile(){ document.getElementById('prof-modal').style.display = 'none'; }
async function saveProfile(){
    const b = { nama: document.getElementById('p-nama').value, kampus: document.getElementById('p-kampus').value, laptop: document.getElementById('p-laptop').value };
    await fetch('/api/profile', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}); closeProfile();
}
async function delMsg(id){ await fetch('/api/del_chat/' + id, {method:'POST'}); const el = document.getElementById('msg-' + id); if(el) el.remove(); const lg = document.getElementById('log-' + id); if(lg) lg.remove(); }"""

PART_JS2 = """
async function sendChat(e){
    e.preventDefault();
    const inp = document.getElementById('cinput'), box = document.getElementById('cbox'), btn = document.getElementById('cbtn'), sp = document.getElementById('vn-img'), llist = document.getElementById('llist');
    const msg = inp.value.trim(); if(!msg) return;
    inp.value = ''; btn.disabled = true; btn.innerText = '...';
    const emp = document.getElementById('empty-chat'); if(emp) emp.remove();
    const tmpId = 'tmp-' + Date.now();
    box.insertAdjacentHTML('afterbegin', `<div class='c-user' id='${tmpId}'><div><b>Kapten:</b> ${msg}</div></div>`);
    const payload = { msg, mode: document.getElementById('cmode').value, model: document.getElementById('cmodel').value, think: document.getElementById('cthink').value };
    const res = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await res.json();
    btn.disabled = false; btn.innerText = 'Kirim';
    if(data.ok){
        const tEl = document.getElementById(tmpId);
        if(tEl){ tEl.id = 'msg-' + data.u_id; tEl.insertAdjacentHTML('beforeend', `<button class='del-x' onclick='delMsg(${data.u_id})'>✕</button>`); }
        box.insertAdjacentHTML('afterbegin', `<div class='c-elysia' id='msg-${data.e_id}'><div><b>Elysia:</b> ${data.elysia}</div><button class='del-x' onclick='delMsg(${data.e_id})'>✕</button></div>`);
        if(llist){ llist.insertAdjacentHTML('afterbegin', `<li id='log-${data.e_id}'><span><b>Elysia:</b> ${data.elysia}</span><small>#${data.e_id}</small></li><li id='log-${data.u_id}'><span><b>Kapten:</b> ${msg}</span><small>#${data.u_id}</small></li>`); }
        if(data.img && !sp.src.endsWith(data.img)){ sp.style.opacity = 0.25; setTimeout(() => { sp.src = data.img; sp.style.opacity = 1; }, 150); }
        if(data.mood){ document.getElementById('m-label').innerText = 'Mood: ' + data.mood.charAt(0).toUpperCase() + data.mood.slice(1); document.getElementById('m-pct').innerText = data.pct + '%'; document.getElementById('m-bar').style.width = data.pct + '%'; }
        if(data.audio){ if(curAudio) curAudio.pause(); curAudio = new Audio(data.audio); curAudio.play(); }
    }
}
async function clearChat(){ await fetch('/api/clear_chat', {method:'POST'}); document.getElementById('cbox').innerHTML = "<div id='empty-chat' style='font-size:11px;opacity:0.8;'>Chat bersih! Yuk sapa Elysia!</div>"; if(document.getElementById('llist')) document.getElementById('llist').innerHTML = ""; }
const cvs = document.getElementById('wind-cvs'), ctx = cvs.getContext('2d');
function rsz(){ cvs.width = window.innerWidth; cvs.height = window.innerHeight; } window.addEventListener('resize', rsz); rsz();
const pt = Array.from({length: 24}, () => ({x:Math.random()*cvs.width,y:Math.random()*cvs.height,r:Math.random()*4+3,vx:Math.random()*1.6+1,vy:Math.random()*0.7+0.3,a:Math.random()*6,va:0.03}));
function drawW(){ ctx.clearRect(0,0,cvs.width,cvs.height); pt.forEach(p=>{ p.x+=p.vx; p.y+=p.vy; p.a+=p.va; if(p.x>cvs.width+10)p.x=-10; if(p.y>cvs.height+10)p.y=-10; ctx.save(); ctx.translate(p.x,p.y); ctx.rotate(p.a); ctx.fillStyle='rgba(255,185,210,0.7)'; ctx.beginPath(); ctx.ellipse(0,0,p.r,p.r*0.55,0,0,Math.PI*2); ctx.fill(); ctx.restore(); }); requestAnimationFrame(drawW); } drawW();
</script></body></html>"""

HTML_PAGE = PART_STYLE + PART_BODY + PART_JS1 + PART_JS2
