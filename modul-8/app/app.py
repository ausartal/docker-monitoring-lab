"""
Flask App — Portal PENS
Dilindungi oleh Keycloak OAuth2 / OIDC.
Dipakai oleh app1 (Portal Mahasiswa) dan app2 (Portal Nilai) via env var.
"""
import os, json, time, secrets
from functools import wraps
from urllib.parse import urlencode
import requests, jwt
from flask import Flask, jsonify, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

KC_URL        = os.environ.get("KEYCLOAK_URL", "http://keycloak:8080")
KC_EXT_URL    = os.environ.get("KEYCLOAK_EXTERNAL_URL", "http://localhost:8180")
REALM         = os.environ.get("KEYCLOAK_REALM", "pens-lab")
CLIENT_ID     = os.environ.get("KEYCLOAK_CLIENT_ID", "flask-app-1")
CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "flask-app-1-secret")
APP_NAME      = os.environ.get("APP_NAME", "Portal PENS")
APP_PORT      = int(os.environ.get("APP_PORT", 5001))

OIDC_BASE     = f"{KC_URL}/realms/{REALM}/protocol/openid-connect"
OIDC_EXT_BASE = f"{KC_EXT_URL}/realms/{REALM}/protocol/openid-connect"
AUTH_URL      = f"{OIDC_EXT_BASE}/auth"
TOKEN_URL     = f"{OIDC_BASE}/token"
USERINFO_URL  = f"{OIDC_BASE}/userinfo"
LOGOUT_URL    = f"{OIDC_EXT_BASE}/logout"
CERTS_URL     = f"{OIDC_BASE}/certs"

_jwks_cache = {"keys": None, "fetched_at": 0}

def get_jwks():
    if _jwks_cache["keys"] and time.time() - _jwks_cache["fetched_at"] < 300:
        return _jwks_cache["keys"]
    try:
        resp = requests.get(CERTS_URL, timeout=5)
        _jwks_cache["keys"] = resp.json()
        _jwks_cache["fetched_at"] = time.time()
        return _jwks_cache["keys"]
    except Exception:
        return _jwks_cache["keys"]

def decode_token(token):
    jwks = get_jwks()
    if not jwks:
        return None
    try:
        header = jwt.get_unverified_header(token)
        key = None
        for k in jwks.get("keys", []):
            if k["kid"] == header["kid"]:
                key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k))
                break
        if not key:
            return None
        return jwt.decode(token, key, algorithms=["RS256"],
                         audience="account",
                         options={"verify_exp": True})
    except Exception as e:
        app.logger.error(f"Token decode error: {e}")
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "access_token" not in session:
            session["next_url"] = request.url
            state = secrets.token_urlsafe(32)
            session["oauth_state"] = state
            params = urlencode({
                "client_id": CLIENT_ID,
                "response_type": "code",
                "scope": "openid profile email",
                "redirect_uri": url_for("callback", _external=True),
                "state": state
            })
            return redirect(f"{AUTH_URL}?{params}")
        claims = decode_token(session["access_token"])
        if not claims:
            session.clear()
            return redirect(url_for("index"))
        request.user = claims
        return f(*args, **kwargs)
    return decorated

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            claims = getattr(request, "user", {})
            realm_roles = claims.get("realm_access", {}).get("roles", [])
            client_roles = claims.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", [])
            if role not in realm_roles + client_roles:
                return jsonify({"error": "forbidden", "required_role": role,
                               "your_roles": realm_roles}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route("/")
def index():
    user = None
    if "access_token" in session:
        user = decode_token(session["access_token"])
    logged_in_html = ""
    if user:
        roles = user.get('realm_access', {}).get('roles', [])
        logged_in_html = f"""
        <div style="background:#e3f2fd;padding:15px;border-radius:8px;margin:10px 0">
            <p>✅ Login sebagai: <strong>{user.get('preferred_username','')}</strong></p>
            <p>Email: {user.get('email','')}</p>
            <p>Roles: {roles}</p>
        </div>
        <a style="background:#2e7d32;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;margin:5px" href="/dashboard">Dashboard</a>
        <a style="background:#1565c0;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;margin:5px" href="/api/me">API /me</a>
        <a style="background:#c62828;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;margin:5px" href="/logout">Logout</a>
        """
    else:
        logged_in_html = '<a style="background:#1565c0;color:white;padding:12px 24px;border-radius:8px;text-decoration:none" href="/dashboard">Login dengan Keycloak</a>'
    return f"""<!DOCTYPE html>
<html><head><title>{APP_NAME}</title>
<style>body{{font-family:sans-serif;max-width:700px;margin:40px auto;padding:20px;background:#f5f5f5;}}
.card{{background:white;border-radius:12px;padding:30px;box-shadow:0 2px 10px rgba(0,0,0,.1);}}</style>
</head><body><div class="card">
<h1>🎓 {APP_NAME}</h1>
<p>Aplikasi ini dilindungi oleh <strong>Keycloak</strong> OAuth2 / OpenID Connect.</p>
{logged_in_html}
<hr><p><small>SSO: login sekali, otomatis login di semua app dalam realm yang sama.</small></p>
</div></body></html>"""

@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if state != session.get("oauth_state"):
        return jsonify({"error": "invalid state"}), 400
    if not code:
        return jsonify({"error": "no code received"}), 400
    try:
        resp = requests.post(TOKEN_URL, data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": url_for("callback", _external=True)
        }, timeout=10)
        if resp.status_code != 200:
            return jsonify({"error": "token exchange failed", "detail": resp.text}), 400
        tokens = resp.json()
        session["access_token"] = tokens["access_token"]
        session["refresh_token"] = tokens.get("refresh_token")
        session["id_token"] = tokens.get("id_token")
        return redirect(session.pop("next_url", url_for("index")))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/dashboard")
@login_required
def dashboard():
    user = request.user
    return f"""<!DOCTYPE html>
<html><head><title>Dashboard</title>
<style>body{{font-family:sans-serif;max-width:700px;margin:40px auto;padding:20px;}}
.card{{background:white;border-radius:12px;padding:30px;box-shadow:0 2px 10px rgba(0,0,0,.1);}}
pre{{background:#263238;color:#80cbc4;padding:15px;border-radius:8px;overflow-x:auto;font-size:12px;}}</style>
</head><body><div class="card">
<h1>📊 Dashboard — {APP_NAME}</h1>
<p>Selamat datang, <strong>{user.get('preferred_username','')}</strong>!</p>
<h3>JWT Claims:</h3>
<pre>{json.dumps(user, indent=2, default=str)}</pre>
<p><a href="/">Kembali</a> | <a href="/admin">Admin Panel</a> | <a href="/logout">Logout</a></p>
</div></body></html>"""

@app.route("/admin")
@login_required
@role_required("admin")
def admin_panel():
    return jsonify({"page": "Admin Panel", "message": "Akses admin berhasil!",
                    "user": request.user.get("preferred_username")})

@app.route("/api/me")
@login_required
def api_me():
    user = request.user
    return jsonify({
        "username": user.get("preferred_username"),
        "email": user.get("email"),
        "name": user.get("name"),
        "realm_roles": user.get("realm_access", {}).get("roles", []),
        "client_roles": user.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", [])
    })

@app.route("/logout")
def logout():
    id_token = session.get("id_token", "")
    session.clear()
    params = urlencode({
        "id_token_hint": id_token,
        "post_logout_redirect_uri": url_for("index", _external=True)
    })
    return redirect(f"{LOGOUT_URL}?{params}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
