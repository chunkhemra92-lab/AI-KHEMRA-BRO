import os
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

APP_VERSION = "1.0.0"
DATA_DIR = Path(os.getenv("STORE_DATA_DIR", "/var/lib/ai-khemra-bro"))
DB_PATH = DATA_DIR / "movie_store.db"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "owner")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-now")
TOPUP_CONTACT = os.getenv("TOPUP_CONTACT", "088 395 1538")
TELEGRAM_URL = os.getenv("TELEGRAM_URL", "https://t.me/moviematlydubber")
DATA_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="MATLY MOVIE STORE", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Noto+Sans+Khmer:wght@400;600;700&display=swap');
:root{--bg:#070b14;--line:rgba(148,163,184,.18);--cyan:#45d9ff;--gold:#f5c451;--muted:#9aa9bd}
.stApp{background:radial-gradient(circle at 50% -15%,rgba(25,118,210,.22),transparent 34rem),var(--bg);color:#f6f9ff;font-family:'Manrope','Noto Sans Khmer',sans-serif}.block-container{max-width:1200px;padding-top:1rem;padding-bottom:4rem}
.hero{padding:30px 22px;border:1px solid rgba(69,217,255,.35);border-radius:26px;background:linear-gradient(145deg,rgba(23,40,69,.94),rgba(8,14,25,.98));box-shadow:0 20px 50px rgba(0,0,0,.22);margin-bottom:14px}.hero h1{font-size:clamp(30px,6vw,58px);margin:0;font-weight:800;letter-spacing:-2px}.hero p{color:var(--cyan);font-weight:700;letter-spacing:1px;margin:.5rem 0 0}.section{font-size:26px;font-weight:800;margin:26px 0 12px}.section small{color:var(--muted);font-size:12px;letter-spacing:1px;margin-left:8px}.card{background:linear-gradient(145deg,#14243a,#0e1727);border:1px solid var(--line);border-radius:18px;padding:12px;height:100%;box-shadow:0 10px 28px rgba(0,0,0,.15)}.card img{border-radius:13px}.price{color:var(--gold);font-size:18px;font-weight:800}.muted{color:var(--muted);font-size:13px}.stButton>button,.stLinkButton a{border-radius:12px;font-weight:800;min-height:44px;background:linear-gradient(100deg,#126bc1,#22bddc);border:1px solid rgba(120,220,255,.25)}.wallet{background:linear-gradient(135deg,#1b3b62,#15243a);border:1px solid rgba(69,217,255,.3);border-radius:16px;padding:15px 18px}.wallet b{font-size:26px;color:var(--gold)}.stTextInput input,.stTextArea textarea,.stNumberInput input{background:#182438!important;color:white!important;border:1px solid #52657f!important;border-radius:10px!important}.stTabs [data-baseweb="tab-list"]{gap:6px;background:rgba(15,23,38,.9);border:1px solid var(--line);border-radius:16px;padding:6px}.stTabs [data-baseweb="tab"]{border-radius:11px;color:#aebbd0;font-weight:800}.stTabs [aria-selected="true"]{background:linear-gradient(100deg,#1976d2,#22bddc);color:#fff}.quick{background:#101d30;border:1px solid var(--line);border-radius:15px;padding:12px;text-align:center}.feature{background:linear-gradient(110deg,rgba(18,107,193,.95),rgba(9,26,49,.96));border:1px solid rgba(69,217,255,.35);border-radius:22px;padding:24px;min-height:190px}.feature h2{font-size:clamp(24px,4vw,42px);margin:8px 0}.feature .badge{color:#ffcf5a;font-weight:800;letter-spacing:.8px}.footer{border-top:1px solid var(--line);margin-top:40px;padding:22px 0;color:var(--muted);font-size:13px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 14px;margin-bottom:12px;background:rgba(8,14,25,.92);border:1px solid var(--line);border-radius:16px;position:sticky;top:8px;z-index:10;backdrop-filter:blur(14px)}.brand{font-size:18px;font-weight:900;letter-spacing:.4px}.brand span{color:var(--cyan)}.toplinks{display:flex;gap:7px;flex-wrap:wrap;justify-content:center}.toplinks span{padding:7px 10px;border-radius:9px;color:#b7c5d8;font-size:12px;font-weight:800}.toplinks span.active{background:linear-gradient(100deg,#1976d2,#22bddc);color:white}.top-actions{display:flex;gap:7px}.top-pill{border:1px solid rgba(245,196,81,.4);color:#ffd66a;border-radius:999px;padding:7px 10px;font-size:12px;font-weight:800}.bottom-nav{display:none}@media(max-width:700px){.topbar{position:relative;top:0;display:block;text-align:center}.brand{margin-bottom:7px}.toplinks{overflow:hidden;flex-wrap:nowrap;justify-content:flex-start}.toplinks span{white-space:nowrap}.top-actions{justify-content:center;margin-top:7px}.bottom-nav{display:flex;position:fixed;left:8px;right:8px;bottom:8px;z-index:20;justify-content:space-around;background:rgba(8,14,25,.96);border:1px solid rgba(69,217,255,.3);border-radius:16px;padding:8px;box-shadow:0 10px 34px rgba(0,0,0,.45)}.bottom-nav div{font-size:11px;color:#b7c5d8;text-align:center;font-weight:800}.bottom-nav .active{color:var(--cyan)}}
</style>
""", unsafe_allow_html=True)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS movies(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,description TEXT DEFAULT '',genre TEXT DEFAULT 'Drama',country TEXT DEFAULT 'Cambodia',poster_url TEXT DEFAULT '',video_url TEXT DEFAULT '',price INTEGER NOT NULL DEFAULT 0,featured INTEGER DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,coins INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS purchases(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL,movie_id INTEGER NOT NULL,price INTEGER NOT NULL,purchased_at TEXT NOT NULL,UNIQUE(customer_id,movie_id),FOREIGN KEY(customer_id) REFERENCES customers(id),FOREIGN KEY(movie_id) REFERENCES movies(id));
        CREATE TABLE IF NOT EXISTS topups(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL,coins INTEGER NOT NULL,reference TEXT DEFAULT '',status TEXT DEFAULT 'pending',created_at TEXT NOT NULL,FOREIGN KEY(customer_id) REFERENCES customers(id));
        """)
        if conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0] == 0:
            now = datetime.utcnow().isoformat(timespec="seconds")
            conn.executemany("INSERT INTO movies(title,description,genre,country,poster_url,video_url,price,featured,created_at) VALUES(?,?,?,?,?,?,?,?,?)", [
                ("ស្នេហ៍ក្រោមពន្លឺព្រះចន្ទ", "រឿងភាគខ្មែរពោរពេញដោយអារម្មណ៍ និងអាថ៌កំបាំង។", "Romance", "Cambodia", "", "", 30, 1, now),
                ("The Last Guardian", "An action adventure movie for the whole family.", "Action", "Hollywood", "", "", 50, 1, now),
                ("កំណត់ហេតុអ្នកក្លាហាន", "រឿងខ្លីបែបប្រវត្តិសាស្ត្រ និងការតស៊ូ។", "Drama", "China", "", "", 20, 0, now),
            ])


def get_customer(name):
    name = (name or "Guest").strip()[:80] or "Guest"
    with db() as conn:
        row = conn.execute("SELECT * FROM customers WHERE name=?", (name,)).fetchone()
        if not row:
            conn.execute("INSERT INTO customers(name,coins,created_at) VALUES(?,?,?)", (name, 0, datetime.utcnow().isoformat(timespec="seconds")))
            row = conn.execute("SELECT * FROM customers WHERE name=?", (name,)).fetchone()
        return row


def movie_rows(search="", genre="All"):
    query, args = "SELECT * FROM movies WHERE 1=1", []
    if search: query += " AND (title LIKE ? OR description LIKE ?)"; args += [f"%{search}%", f"%{search}%"]
    if genre != "All": query += " AND genre=?"; args.append(genre)
    query += " ORDER BY featured DESC,id DESC"
    with db() as conn: return conn.execute(query, args).fetchall()


def is_owned(customer_id, movie_id):
    with db() as conn: return bool(conn.execute("SELECT 1 FROM purchases WHERE customer_id=? AND movie_id=?", (customer_id, movie_id)).fetchone())


def buy_movie(customer_id, movie):
    with db() as conn:
        current = conn.execute("SELECT coins FROM customers WHERE id=?", (customer_id,)).fetchone()[0]
        if current < movie["price"]: return False, "កាក់មិនគ្រប់ទេ។ សូមបញ្ចូលកាក់ជាមុន។"
        try:
            conn.execute("UPDATE customers SET coins=coins-? WHERE id=?", (movie["price"], customer_id))
            conn.execute("INSERT INTO purchases(customer_id,movie_id,price,purchased_at) VALUES(?,?,?,?)", (customer_id, movie["id"], movie["price"], datetime.utcnow().isoformat(timespec="seconds")))
            return True, "ទិញរឿងបានជោគជ័យ។"
        except sqlite3.IntegrityError: return True, "អ្នកបានទិញរឿងនេះរួចហើយ។"


def image_for(movie):
    return movie["poster_url"] or "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=900&q=80"


def valid_url(value):
    parsed = urlparse(value or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


init_db()
if "customer_name" not in st.session_state: st.session_state.customer_name = ""
if "admin" not in st.session_state: st.session_state.admin = False
st.markdown('<div class="topbar"><div class="brand">MOVIE.<span>MATLYDUBBER</span></div><div class="toplinks"><span class="active">ទំព័រដើម</span><span>Movie Feed</span><span>🔥 HOT</span><span>REELS</span><span>FREE</span><span>កាតាឡុក</span></div><div class="top-actions"><span class="top-pill">VIP $10</span><span class="top-pill">🪙 0</span></div></div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🎬 MATLY MOVIE STORE</h1><p>មើលរឿងថ្មីៗ ជាភាសាខ្មែរ · ទិញមើលបានភ្លាមៗ</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### គណនីអ្នកមើល")
    entered = st.text_input("ឈ្មោះអ្នកប្រើ", value=st.session_state.customer_name, placeholder="ឧ. Khemra")
    if st.button("ចូលប្រើ / ប្តូរគណនី", use_container_width=True): st.session_state.customer_name = entered.strip() or "Guest"; st.rerun()
    customer = get_customer(st.session_state.customer_name or "Guest")
    st.markdown(f'<div class="wallet">កាក់របស់អ្នក<br><b>🪙 {customer["coins"]:,}</b></div>', unsafe_allow_html=True)
    st.divider(); st.caption("ម្ចាស់ហាង")
    admin_user = st.text_input("Username", key="admin_user")
    admin_pass = st.text_input("Password", type="password", key="admin_pass")
    if st.button("ចូល Admin", use_container_width=True):
        if admin_user == ADMIN_USERNAME and admin_pass == ADMIN_PASSWORD: st.session_state.admin = True; st.success("ចូល Admin បាន")
        else: st.error("Username ឬ Password មិនត្រឹមត្រូវ")
    if st.session_state.admin and st.button("ចេញពី Admin", use_container_width=True): st.session_state.admin = False; st.rerun()

customer = get_customer(st.session_state.customer_name or "Guest")
tabs = st.tabs(["🏠 កាតាឡុក", "🪙 បញ្ចូលកាក់", "🎞️ រឿងដែលបានទិញ"] + (["⚙️ Admin Studio"] if st.session_state.admin else []))

with tabs[0]:
    all_movies = movie_rows()
    featured = all_movies[0] if all_movies else None
    if featured:
        left, right = st.columns([2.2, 1])
        with left:
            st.markdown(f'<div class="feature"><div class="badge">🔥 កំពុងពេញនិយម · MOVIE FEED</div><h2>{featured["title"]}</h2><p>{featured["description"] or "មើលរឿងពេញនិយមថ្មីៗនៅទីនេះ។"}</p><p>★ 9.8 · 2026 · {featured["genre"]}</p></div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="quick"><b>VIP MEMBERSHIP</b><br><span class="price">$10 / month</span><br><span class="muted">មើលរឿងពិសេស និងរឿងថ្មីៗ</span></div>', unsafe_allow_html=True)
            if featured["video_url"]: st.link_button("▶️ ទស្សនាឥឡូវ", featured["video_url"], use_container_width=True)
    st.markdown('<div class="section">ចូលមើលលឿន <small>QUICK ACCESS</small></div>', unsafe_allow_html=True)
    q1,q2,q3,q4,q5,q6 = st.columns(6)
    quick_items = [(q1,"🔥","កំពុងពេញនិយម"),(q2,"🆕","រឿងថ្មី"),(q3,"🎬","រឿងដុំ"),(q4,"📺","រឿងភាគ"),(q5,"⚡","Anime"),(q6,"🆓","Free")]
    for col, icon, label in quick_items:
        with col: st.markdown(f'<div class="quick">{icon}<br><b>{label}</b></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1]); search = c1.text_input("ស្វែងរករឿង", placeholder="ស្វែងរកចំណងជើង ឬប្រភេទ...")
    with db() as conn: genres = [r[0] for r in conn.execute("SELECT DISTINCT genre FROM movies ORDER BY genre").fetchall()]
    genre = c2.selectbox("ប្រភេទ", ["All"] + genres)
    filtered = movie_rows(search, genre)

    def render_section(title, subtitle, rows, key_prefix):
        st.markdown(f'<div class="section">{title} <small>{subtitle}</small></div>', unsafe_allow_html=True)
        if not rows: st.caption("មិនទាន់មានរឿងនៅផ្នែកនេះទេ។"); return
        for row_start in range(0, min(len(rows), 6), 3):
            cols = st.columns(3)
            for col, movie in zip(cols, rows[row_start:row_start+3]):
                with col:
                    owned = is_owned(customer["id"], movie["id"])
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.image(image_for(movie), use_container_width=True)
                    badge = "FREE 100%" if movie["price"] == 0 else ("💎 VIP" if movie["featured"] else "NEW")
                    st.caption(f"{badge} · {movie['genre']} · ★ 9.2")
                    st.markdown(f"### {movie['title']}")
                    st.caption(f"2026 · {movie['country']}")
                    if owned or movie["price"] == 0:
                        if movie["video_url"]: st.link_button("▶️ មើលរឿង", movie["video_url"], use_container_width=True)
                        else: st.success("ឥតគិតថ្លៃ" if movie["price"] == 0 else "Admin មិនទាន់ដាក់ Video URL")
                    elif st.button(f"🪙 {movie['price']} · ទិញ", key=f"{key_prefix}_{movie['id']}", use_container_width=True):
                        ok, msg = buy_movie(customer["id"], movie); (st.success if ok else st.warning)(msg); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    render_section("រឿងទើបបញ្ចូលថ្មីៗ", "LATEST RELEASES", filtered or all_movies, "latest")
    render_section("រឿងទស្សនាឥតគិតថ្លៃ", "100% FREE", [m for m in all_movies if m["price"] == 0], "free")
    render_section("កំពុងពេញនិយម", "TRENDING NOW", [m for m in all_movies if m["featured"]] or all_movies, "trending")
    render_section("រឿងដុំ Movies", "MOVIES", [m for m in all_movies if m["genre"] in {"Action", "Drama"}] or all_movies, "movies")
    render_section("រឿងភាគ TV Series", "TV SERIES", [m for m in all_movies if m["genre"] in {"Romance", "Drama"}] or all_movies, "series")
    render_section("🎌 Anime & គំនូរជីវចល", "ANIME & DONGHUA", [m for m in all_movies if m["genre"] == "Anime"], "anime")
    st.markdown('<div class="footer"><b>MATLY MOVIE STORE</b><br>ទំព័រដើម · វីដេអូខ្លី · បញ្ចូលកាក់ · ស្វែងរក · ម៉ឺនុយ<br>Telegram: t.me/moviematlydubber · 088 395 1538<br><br>ABA Pay · Bakong · KHQR</div>', unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<div class="section">បញ្ចូលកាក់សម្រាប់ទិញរឿង</div>', unsafe_allow_html=True)
    st.info(f"សូមផ្ញើប្រាក់ទៅ ABA Pay / KHQR របស់ម្ចាស់ហាង ហើយទាក់ទង Telegram ឬទូរស័ព្ទ {TOPUP_CONTACT} ដើម្បីឲ្យ Admin បន្ថែមកាក់។")
    st.link_button("💬 ទាក់ទងតាម Telegram", TELEGRAM_URL)
    with st.form("topup_request"):
        amount = st.number_input("ចំនួនកាក់ដែលចង់បញ្ចូល", min_value=10, value=100, step=10); reference = st.text_input("លេខយោងការទូទាត់ (បើមាន)")
        if st.form_submit_button("ផ្ញើសំណើបញ្ចូលកាក់"):
            with db() as conn: conn.execute("INSERT INTO topups(customer_id,coins,reference,created_at) VALUES(?,?,?,?)", (customer["id"], int(amount), reference.strip(), datetime.utcnow().isoformat(timespec="seconds")))
            st.success("បានផ្ញើសំណើ។ Admin នឹងពិនិត្យ និងបន្ថែមកាក់ឲ្យអ្នក។")

with tabs[2]:
    st.markdown('<div class="section">រឿងដែលអ្នកបានទិញ</div>', unsafe_allow_html=True)
    with db() as conn: owned_rows = conn.execute("SELECT m.*,p.price,p.purchased_at FROM purchases p JOIN movies m ON m.id=p.movie_id WHERE p.customer_id=? ORDER BY p.id DESC", (customer["id"],)).fetchall()
    if not owned_rows: st.info("អ្នកមិនទាន់បានទិញរឿងទេ។")
    for movie in owned_rows:
        a, b = st.columns([1, 3]); a.image(image_for(movie), use_container_width=True); b.subheader(movie["title"]); b.caption(f"បានទិញ {movie['purchased_at']} · 🪙 {movie['price']}"); b.write(movie["description"] or "")
        if movie["video_url"]: b.link_button("▶️ មើលរឿង", movie["video_url"])

if st.session_state.admin:
    with tabs[3]:
        st.markdown('<div class="section">Admin Studio — គ្រប់គ្រងហាង</div>', unsafe_allow_html=True)
        with st.form("add_movie", clear_on_submit=True):
            st.subheader("បញ្ចូលរឿងថ្មី"); title = st.text_input("ចំណងជើង *"); description = st.text_area("ការពិពណ៌នា")
            a,b,c,d = st.columns(4); genre_new = a.text_input("ប្រភេទ", "Drama"); country = b.text_input("ប្រទេស", "Cambodia"); price = c.number_input("តម្លៃកាក់", min_value=0, value=20, step=5); featured = d.checkbox("ដាក់ជា HOT")
            poster_url = st.text_input("Poster URL (https://...)"); video_url = st.text_input("Video URL (https://...)")
            if st.form_submit_button("បោះពុម្ពរឿង"):
                if not title.strip(): st.error("សូមបញ្ចូលចំណងជើង")
                elif poster_url and not valid_url(poster_url): st.error("Poster URL មិនត្រឹមត្រូវ")
                elif video_url and not valid_url(video_url): st.error("Video URL មិនត្រឹមត្រូវ")
                else:
                    with db() as conn: conn.execute("INSERT INTO movies(title,description,genre,country,poster_url,video_url,price,featured,created_at) VALUES(?,?,?,?,?,?,?,?,?)", (title.strip(), description.strip(), genre_new.strip() or "Drama", country.strip() or "Cambodia", poster_url.strip(), video_url.strip(), int(price), int(featured), datetime.utcnow().isoformat(timespec="seconds")))
                    st.success("បានបោះពុម្ពរឿងថ្មី"); st.rerun()
        st.divider(); st.subheader("សំណើបញ្ចូលកាក់")
        with db() as conn: topups = conn.execute("SELECT t.*,c.name FROM topups t JOIN customers c ON c.id=t.customer_id WHERE t.status='pending' ORDER BY t.id DESC").fetchall()
        for topup in topups:
            st.write(f"{topup['name']} · 🪙 {topup['coins']} · {topup['reference'] or 'គ្មានលេខយោង'}"); x, y = st.columns(2)
            if x.button("អនុម័ត", key=f"approve_{topup['id']}"):
                with db() as conn: conn.execute("UPDATE customers SET coins=coins+? WHERE id=?", (topup["coins"], topup["customer_id"])); conn.execute("UPDATE topups SET status='approved' WHERE id=?", (topup["id"],))
                st.rerun()
            if y.button("បដិសេធ", key=f"reject_{topup['id']}"):
                with db() as conn: conn.execute("UPDATE topups SET status='rejected' WHERE id=?", (topup["id"],))
                st.rerun()

st.markdown('<div class="bottom-nav"><div class="active">⌂<br>ទំព័រដើម</div><div>▣<br>វីដេអូខ្លី</div><div>🪙<br>បញ្ចូលកាក់</div><div>⌕<br>ស្វែងរក</div><div>☰<br>ម៉ឺនុយ</div></div>', unsafe_allow_html=True)
st.divider(); st.caption(f"MATLY MOVIE STORE v{APP_VERSION} · ទិញមាតិកាដោយសុវត្ថិភាព និងគោរពសិទ្ធិអ្នកកាន់កាប់មាតិកា")
