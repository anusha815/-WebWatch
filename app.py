import os, sqlite3
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from flask import Flask, flash, redirect, render_template, request, url_for

ROOT = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY", "webwatch-demo-key"),
                  DATABASE=os.environ.get("WEBWATCH_DATABASE", os.path.join(ROOT, "webwatch.db")))

def db_connect():
    con = sqlite3.connect(app.config["DATABASE"])
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db_connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS websites(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS checks(
            id INTEGER PRIMARY KEY AUTOINCREMENT, website_id INTEGER NOT NULL,
            status TEXT NOT NULL, status_code INTEGER, response_time REAL,
            checked_at TEXT NOT NULL, message TEXT,
            FOREIGN KEY(website_id) REFERENCES websites(id))""")

def normalize_url(value):
    value = (value or "").strip()
    if not value:
        raise ValueError("Please enter a website URL.")
    if not urlparse(value).scheme:
        value = "https://" + value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Enter a valid http or https website address.")
    return value

def check_website(url, timeout=8):
    started = datetime.now(timezone.utc)
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True,
                                headers={"User-Agent": "WebWatch-Uptime-Monitor/1.0"})
        ms = round((datetime.now(timezone.utc)-started).total_seconds()*1000, 2)
        ok = response.status_code < 400
        return {"status": "Online" if ok else "Offline", "status_code": response.status_code,
                "response_time": ms, "message": "Website responded successfully." if ok
                else f"Website returned HTTP {response.status_code}."}
    except requests.RequestException as exc:
        ms = round((datetime.now(timezone.utc)-started).total_seconds()*1000, 2)
        return {"status":"Offline", "status_code":None, "response_time":ms, "message":str(exc)[:250]}

def save_check(site_id, result):
    with db_connect() as con:
        con.execute("""INSERT INTO checks(website_id,status,status_code,response_time,checked_at,message)
                       VALUES(?,?,?,?,?,?)""",
                    (site_id,result["status"],result["status_code"],result["response_time"],
                     datetime.now(timezone.utc).isoformat(timespec="seconds"),result["message"]))

def dashboard_data():
    with db_connect() as con:
        sites = con.execute("""SELECT w.*,
          c.status latest_status,c.status_code latest_code,c.response_time latest_response_time,
          c.checked_at latest_checked_at
          FROM websites w LEFT JOIN checks c ON c.id=(SELECT id FROM checks
          WHERE website_id=w.id ORDER BY id DESC LIMIT 1) ORDER BY w.id DESC""").fetchall()
        history = con.execute("""SELECT c.*,w.name FROM checks c JOIN websites w
          ON w.id=c.website_id ORDER BY c.id DESC LIMIT 10""").fetchall()
    total=len(sites); online=sum(s["latest_status"]=="Online" for s in sites)
    offline=sum(s["latest_status"]=="Offline" for s in sites)
    return sites,history,{"total":total,"online":online,"offline":offline,"unchecked":total-online-offline}

@app.route("/")
def index():
    sites,history,stats=dashboard_data()
    return render_template("index.html", websites=sites, history=history, stats=stats)

@app.post("/add")
def add_website():
    name=(request.form.get("name") or "").strip()
    try:
        url=normalize_url(request.form.get("url"))
        if not name: name=urlparse(url).netloc
        with db_connect() as con:
            con.execute("INSERT INTO websites(name,url,created_at) VALUES(?,?,?)",
                        (name,url,datetime.now(timezone.utc).isoformat(timespec="seconds")))
        flash("Website added. Run a check to view its status.","success")
    except ValueError as e: flash(str(e),"error")
    except sqlite3.IntegrityError: flash("This website is already being monitored.","error")
    return redirect(url_for("index"))

@app.post("/check/<int:site_id>")
def run_check(site_id):
    with db_connect() as con:
        site=con.execute("SELECT * FROM websites WHERE id=?",(site_id,)).fetchone()
    if site is None:
        flash("Website not found.","error")
    else:
        result=check_website(site["url"]); save_check(site_id,result)
        flash(f'{site["name"]}: {result["status"]} — {result["response_time"]} ms',
              "success" if result["status"]=="Online" else "error")
    return redirect(url_for("index"))

@app.post("/check-all")
def check_all():
    with db_connect() as con: sites=con.execute("SELECT * FROM websites").fetchall()
    for site in sites: save_check(site["id"],check_website(site["url"]))
    flash(f"Checked {len(sites)} website(s).","success" if sites else "error")
    return redirect(url_for("index"))

@app.post("/delete/<int:site_id>")
def delete_website(site_id):
    with db_connect() as con:
        con.execute("DELETE FROM checks WHERE website_id=?",(site_id,))
        con.execute("DELETE FROM websites WHERE id=?",(site_id,))
    flash("Website removed.","success")
    return redirect(url_for("index"))

@app.get("/health")
def health():
    return {"status":"ok","service":"WebWatch"},200

init_db()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
