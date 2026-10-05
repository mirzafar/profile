"""Tornado backend for the profile mini-project.

Run:  python app.py  [--port=8888]
Only dependency outside the stdlib is `tornado`.

Admin bootstrap (first run creates one admin):
    ADMIN_LOGIN     (default: admin)
    ADMIN_EMAIL     (default: admin@example.com)
    ADMIN_PASSWORD  (default: random, printed to console)
"""
import os
import re
import time
import secrets

import tornado.ioloop
import tornado.web
import tornado.auth

import db
import i18n
from settings import settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GOOGLE_CLIENT_ID = settings.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = settings.get('GOOGLE_CLIENT_SECRET')

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d\s\-()]{10,20}$")
LOGIN_RE = re.compile(r"^[A-Za-z0-9._-]{3,32}$")  # Latin only

# very small in-memory per-IP rate limiter for the public request form
_RL = {}
RL_WINDOW = 600  # seconds
RL_MAX = 6  # max submissions per window per IP


def rate_ok(ip):
    now = time.time()
    hits = [t for t in _RL.get(ip, []) if now - t < RL_WINDOW]
    if len(hits) >= RL_MAX:
        _RL[ip] = hits
        return False
    hits.append(now)
    _RL[ip] = hits
    return True


def fmt_date(ts):
    return time.strftime("%d.%m.%Y %H:%M", time.localtime(ts))


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("uid")
        if not uid:
            return None
        try:
            return db.get_user_by_id(int(uid))
        except (ValueError, TypeError):
            return None

    @property
    def lang(self):
        lang = self.get_cookie("lang")
        return lang if lang in i18n.LANGS else i18n.DEFAULT_LANG

    def render(self, template, **kwargs):
        ctx = dict(
            t=i18n.make_translator(self.lang),
            lang=self.lang,
            service_label=lambda s: i18n.service_label(s, self.lang),
            status_label=lambda s: i18n.status_label(s, self.lang),
            fmt_date=fmt_date,
            current_user=self.current_user,
            next_uri=self.request.uri,
        )
        ctx.update(kwargs)
        super().render(template, **ctx)


class LangHandler(BaseHandler):
    def get(self):
        lang = self.get_argument("lang", i18n.DEFAULT_LANG)
        if lang in i18n.LANGS:
            self.set_cookie("lang", lang)
        nxt = self.get_argument("next", "/")
        if not nxt.startswith("/"):
            nxt = "/"
        self.redirect(nxt)


class MainHandler(BaseHandler):
    """Serve the landing page (static HTML) at /."""

    def get(self):
        path = os.path.join(BASE_DIR, "static", "index.html")
        with open(path, "rb") as f:
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.write(f.read())


class RequestApiHandler(BaseHandler):
    """Public endpoint for the landing contact form. Anonymous allowed."""

    def check_xsrf_cookie(self):
        # public form from a static page; protected by honeypot + rate limit
        pass

    def post(self):
        # honeypot: bots fill hidden "website" field
        if self.get_argument("website", ""):
            self.set_status(204)
            return
        ip = self.request.remote_ip
        if not rate_ok(ip):
            self.set_status(429)
            self.write({"ok": False, "error": "rate_limited"})
            return

        name = self.get_argument("name", "").strip()
        phone = self.get_argument("phone", "").strip()
        email = self.get_argument("email", "").strip()
        service = self.get_argument("service", "other").strip()
        message = self.get_argument("message", "").strip()

        if not name or not phone or not email:
            self.set_status(400)
            self.write({"ok": False, "error": "fields"})
            return
        if not PHONE_RE.match(phone):
            self.set_status(400)
            self.write({"ok": False, "error": "phone"})
            return
        if not EMAIL_RE.match(email):
            self.set_status(400)
            self.write({"ok": False, "error": "email"})
            return

        uid = int(self.current_user["id"]) if self.current_user else None
        db.create_request(name, phone, email, service, message, user_id=uid)
        self.write({"ok": True})


class RegisterHandler(BaseHandler):
    """Registration is Google-only now."""

    def get(self):
        self.render("register.html", google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET))


class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html", error=None, form={},
                    google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET))

    def post(self):
        login = self.get_argument("login", "").strip()
        password = self.get_argument("password", "")
        user = db.get_user_by_login(login) or (
            db.get_user_by_login(login.lower()) if login else None
        )
        if (not user or not user["password_hash"]
            or not db.verify_password(password, user["salt"], user["password_hash"])):
            self.render("login.html", error="err_bad_login", form={"login": login},
                        google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET))
            return
        self.set_secure_cookie("uid", str(user["id"]))
        self.redirect("/admin" if user["role"] == "admin" else "/cabinet")


class GoogleAuthHandler(BaseHandler, tornado.auth.GoogleOAuth2Mixin):
    async def get(self):
        if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
            t = i18n.make_translator(self.lang)
            self.render("message.html", title=t("google_off_title"), text=t("google_off_text"))
            return
        redirect_uri = f"{settings.BASE_URL}/auth/google"
        if self.get_argument("code", False):
            access = await self.get_authenticated_user(
                redirect_uri=redirect_uri, code=self.get_argument("code"))
            info = await self.oauth2_request(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                access_token=access["access_token"])
            email = (info.get("email") or "").strip().lower()
            sub = info.get("id")
            name = info.get("name")
            if not email or not sub:
                raise tornado.web.HTTPError(400, "Google did not return an email")
            user = db.get_user_by_google_sub(sub) or db.get_user_by_email(email)
            if user:
                if not user["google_sub"]:
                    db.link_google(user["id"], sub, name)
                uid = user["id"]
            else:
                uid = db.create_user(email=email, name=name, google_sub=sub, role="user")
            self.set_secure_cookie("uid", str(uid))
            self.redirect("/cabinet")
        else:
            # NOTE: authorize_redirect() is NOT a coroutine in Tornado 6.x —
            # it performs the redirect and returns None, so it must not be awaited.
            self.authorize_redirect(
                redirect_uri=redirect_uri,
                client_id=GOOGLE_CLIENT_ID,
                scope=["openid", "email", "profile"],
                response_type="code",
                extra_params={"approval_prompt": "auto"},
            )


class LogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("uid")
        self.redirect("/")


class CabinetHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        reqs = db.get_requests_for_user(int(self.current_user["id"]))
        rows = []
        for r in reqs:
            rows.append({"req": r, "notes": db.get_notes(r["id"], only_visible=True)})
        notice = self.get_argument("m", None)
        self.render("cabinet.html", rows=rows, error=None, notice=notice)


class ChangePasswordHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        new = self.get_argument("new_password", "")
        if len(new) < 6:
            reqs = db.get_requests_for_user(int(self.current_user["id"]))
            rows = [{"req": r, "notes": db.get_notes(r["id"], only_visible=True)} for r in reqs]
            self.render("cabinet.html", rows=rows, error="err_pw_short", notice=None)
            return
        db.update_password(int(self.current_user["id"]), new)
        self.redirect("/cabinet?m=ok_pw_changed")


# ---------- admin ----------

def admin_only(method):
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            self.redirect("/login")
            return
        if self.current_user["role"] != "admin":
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)

    return wrapper


class AdminDashboardHandler(BaseHandler):
    @admin_only
    def get(self):
        self.render("admin_dashboard.html", counts=db.status_counts())


class AdminRequestsHandler(BaseHandler):
    @admin_only
    def get(self):
        status = self.get_argument("status", "") or None
        query = self.get_argument("q", "").strip() or None
        email = self.get_argument("email", "").strip() or None
        try:
            page = max(1, int(self.get_argument("page", "1")))
        except ValueError:
            page = 1
        per = 25
        offset = (page - 1) * per
        total = db.count_requests(status=status, query=query, email=email)
        reqs = db.list_requests(status=status, query=query, email=email, limit=per, offset=offset)
        rows = []
        for r in reqs:
            user = db.get_user_by_id(r["user_id"]) if r["user_id"] else None
            rows.append({"req": r, "user": user, "notes": db.get_notes(r["id"])})
        pages = max(1, (total + per - 1) // per)
        self.render(
            "admin_requests.html",
            rows=rows, status=status or "", query=query or "", email=email or "",
            page=page, pages=pages, total=total,
            statuses=db.STATUSES, notice=self.get_argument("m", None),
        )


class AdminSetStatusHandler(BaseHandler):
    @admin_only
    def post(self, request_id):
        status = self.get_argument("status", "")
        db.set_status(int(request_id), status)
        self.redirect(self.get_argument("next", "/admin/requests") + "?m=ok_status")


class AdminAddNoteHandler(BaseHandler):
    @admin_only
    def post(self, request_id):
        text = self.get_argument("text", "").strip()
        visible = bool(self.get_argument("visible", ""))
        if text:
            db.add_note(int(request_id), self.current_user["nickname"], text, visible)
        self.redirect(self.get_argument("next", "/admin/requests") + "?m=ok_note")


def seed_admin():
    login = settings.ADMIN_LOGIN
    email = settings.ADMIN_EMAIL
    if db.get_user_by_login(login) or db.get_user_by_login(email):
        return
    password = settings.ADMIN_PASSWORD
    generated = False
    if not password:
        password = secrets.token_urlsafe(9)
        generated = True
    db.create_user(email=email, nickname=login, phone="+70000000000", password=password, role="admin")
    print("=" * 56)
    print("  Admin account created:")
    print(f"    login:    {login}")
    print(f"    email:    {email}")
    if generated:
        print(f"    password: {password}   <-- save it, shown once")
    else:
        print("    password: (from ADMIN_PASSWORD)")
    print("=" * 56)


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/setlang", LangHandler),
            (r"/api/requests", RequestApiHandler),
            (r"/register", RegisterHandler),
            (r"/login", LoginHandler),
            (r"/auth/google", GoogleAuthHandler),
            (r"/logout", LogoutHandler),
            (r"/cabinet", CabinetHandler),
            (r"/cabinet/password", ChangePasswordHandler),
            (r"/admin", AdminDashboardHandler),
            (r"/admin/requests", AdminRequestsHandler),
            (r"/admin/requests/([0-9]+)/status", AdminSetStatusHandler),
            (r"/admin/requests/([0-9]+)/note", AdminAddNoteHandler),
        ],
        template_path=os.path.join(BASE_DIR, "templates"),
        static_path=os.path.join(BASE_DIR, "static"),
        static_url_prefix="/static/",
        cookie_secret=settings.COOKIE_SECRET or secrets.token_hex(32),
        xsrf_cookies=True,
        login_url="/login",
        google_oauth={"key": GOOGLE_CLIENT_ID, "secret": GOOGLE_CLIENT_SECRET},
        debug=settings.DEBUG,
    )


def main():
    db.init_db()
    seed_admin()
    app = make_app()
    app.listen(settings.PORT)
    print(f"Serving on http://localhost:{settings.PORT}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
