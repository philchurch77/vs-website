"""Throwaway end-to-end HTTP QA for the consolidation-redesign branch.

Drives the real dev server (CSRF and middleware included, unlike the
Django test client). Uses placeholder data only — no pupil-like names.
Run with the dev server up on 127.0.0.1:8765, then delete this file.
"""
import http.cookiejar
import re
import sys
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8765"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))


class Session:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def get(self, path, follow=True):
        req = urllib.request.Request(BASE + path)
        try:
            resp = self.opener.open(req)
            return resp.status, resp.read().decode("utf-8", "replace"), resp.url
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace"), e.url

    def post(self, path, data, referer=None):
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(BASE + path, data=body)
        req.add_header("Referer", referer or (BASE + path))
        try:
            resp = self.opener.open(req)
            return resp.status, resp.read().decode("utf-8", "replace"), resp.url
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace"), e.url

    def csrf(self, path):
        status, html, _ = self.get(path)
        m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
        return m.group(1) if m else None


def main():
    suffix = sys.argv[1] if len(sys.argv) > 1 else "1"
    owner = Session()
    intruder = Session()

    # 1. Logged-out access
    status, html, _ = owner.get("/")
    check("home renders logged out", status == 200 and "Virtual School" in html)
    status, _, url = owner.get("/flashcards/")
    check("flashcards redirects anon to login", status == 200 and "/users/login/" in url, url)
    status, _, url = owner.get("/tolerance/")
    check("tolerance redirects anon to login", status == 200 and "/users/login/" in url, url)
    status, html, _ = owner.get("/posts/")
    check("posts public", status == 200)
    status, html, _ = owner.get("/posts/?page=999")
    check("posts page=999 clamps (no error)", status == 200)
    status, html, _ = owner.get("/resources/")
    check("resources public", status == 200)

    # 2. Register (this crashed before the branch)
    token = owner.csrf("/users/register/")
    check("register page serves CSRF form", bool(token))
    status, html, url = owner.post("/users/register/", {
        "csrfmiddlewaretoken": token,
        "username": f"vera_owner_{suffix}",
        "password1": "Testpass-123-qa",
        "password2": "Testpass-123-qa",
    })
    check("register creates user + redirects to posts", url.endswith("/posts/"), url)

    # 3. Authenticated pages render with redesign markup
    status, html, _ = owner.get("/flashcards/")
    check("flashcards page renders", status == 200 and 'id="chat-messages"' in html,
          "json_script present" if 'id="chat-messages"' in html else "json_script MISSING")
    check("flashcards uses vendored marked", "/static/js/vendor/marked.min.js" in html)
    check("flashcards loads shared chat.js", "/static/js/chat.js" in html)
    status, html, _ = owner.get("/evaluation/")
    check("evaluation page renders", status == 200 and "Training Evaluation" in html)
    check("evaluation history drawer is HTMX-driven", 'hx-get="/evaluation/chat_history_partial/"' in html)

    # 4. Tolerance: create map, view detail, intruder isolation, delete
    token = owner.csrf("/tolerance/")
    status, html, url = owner.post("/tolerance/", {
        "csrfmiddlewaretoken": token,
        "pupil_name": "Test Pupil A",
        "week_commencing": "2026-06-08",
        "class_or_year_group": "Year 5",
        "key_adults": "QA",
    })
    m = re.search(r"/tolerance/weekly/(\d+)/", url)
    check("create weekly map redirects to detail", bool(m), url)
    pk = m.group(1) if m else None

    if pk:
        status, html, _ = owner.get(f"/tolerance/weekly/{pk}/")
        check("owner sees own map detail", status == 200 and "Test Pupil A" in html)

        # intruder
        token_i = intruder.csrf("/users/register/")
        intruder.post("/users/register/", {
            "csrfmiddlewaretoken": token_i,
            "username": f"vera_intruder_{suffix}",
            "password1": "Testpass-123-qa",
            "password2": "Testpass-123-qa",
        })
        status, html, _ = intruder.get(f"/tolerance/weekly/{pk}/")
        check("intruder gets 404 on owner's map", status == 404, f"status={status}")
        check("intruder page leaks no pupil name", "Test Pupil A" not in html)

        # owner deletes
        token = owner.csrf(f"/tolerance/weekly/{pk}/")
        status, _, url = owner.post(f"/tolerance/weekly/{pk}/delete/", {
            "csrfmiddlewaretoken": token,
        })
        check("owner can delete own map", url.endswith("/tolerance/"), url)

    # 5. Training request: invalid email rejected, valid succeeds
    token = owner.csrf("/training/trainingrequest/")
    status, html, url = owner.post("/training/trainingrequest/", {
        "csrfmiddlewaretoken": token,
        "title": f"Vera QA test {suffix}",
        "body": "QA run",
        "email": "not-an-email",
    })
    check("training rejects bad email (form re-rendered)", status == 200 and "field-error" in html)
    token = owner.csrf("/training/trainingrequest/")
    status, html, url = owner.post("/training/trainingrequest/", {
        "csrfmiddlewaretoken": token,
        "title": f"Vera QA test {suffix}",
        "body": "QA run",
        "email": "qa@example.org",
    })
    ok = url.endswith("/training/trainingrequest/")
    status2, html2, _ = owner.get("/training/trainingrequest/")
    check("training valid submit redirects", ok, url)

    # 6. SDQ scoring renders, nothing persisted
    token = owner.csrf("/sdq/")
    data = {"csrfmiddlewaretoken": token}
    data.update({f"q{i}": "1" for i in range(1, 26)})
    status, html, _ = owner.post("/sdq/", data)
    check("SDQ scores render", status == 200 and "score-card" in html and "Total Difficulties" in html)

    # 7. Evaluation reset endpoint responds
    status, html, _ = owner.get("/evaluation/")  # page sets session state
    req = urllib.request.Request(BASE + "/evaluation/reset-chat-session/", data=b"")
    try:
        resp = owner.opener.open(req)
        check("reset-chat-session responds ok", resp.status == 200)
    except urllib.error.HTTPError as e:
        check("reset-chat-session responds ok", False, f"status={e.code}")

    # 8. Logout
    token = owner.csrf("/posts/")
    status, _, url = owner.post("/users/logout/", {"csrfmiddlewaretoken": token},
                                referer=BASE + "/posts/")
    check("logout redirects to posts", url.endswith("/posts/"), url)
    status, _, url = owner.get("/flashcards/")
    check("after logout flashcards requires login again", "/users/login/" in url, url)

    failures = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failures)}/{len(RESULTS)} checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
