"""Local browser shell for the same cooking_core used by Ren'Py."""

import json
import sys
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from game.systems import cooking_core  # noqa: E402

INGREDIENTS, RECIPES, CONFIG = cooking_core.load_tables()
SAVE = ROOT / ".sessions.json"
SESSIONS = json.loads(SAVE.read_text(encoding="utf-8")) if SAVE.exists() else {}


def summary(view):
    result = {"kind": view["kind"], "target": view.get("target"),
              "ingredient_count": view["stats"]["ingredient_count"],
              "fixed_total": view["stats"]["fixed_total"]}
    if view["kind"] == "recipe":
        result["candidates"] = [{"id": c["recipe"]["id"], "name": c["recipe"]["name"],
                                 "spec": c["recipe"]["spec"], "conflict": c["conflict"],
                                 "target": c["target"], "budget": c["recipe"]["Budget"],
                                 "status": c["recipe"]["status"]} for c in view["candidates"]]
    elif view["kind"] == "processed":
        result["item"] = view["item"]
    return result


class Handler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/data":
            return self._json({"ingredients": [{"id": name, "fixed": row["fixed"],
                                                  "categories": row["categories"], "processed": row["processed"]}
                                                 for name, row in INGREDIENTS.items() if row["fixed"] is not None],
                               "recipe_count": len(RECIPES), "specs": CONFIG["specs"]})
        if url.path == "/api/session":
            session_id = parse_qs(url.query).get("id", [None])[0]
            session = SESSIONS.get(session_id)
            if session is None:
                return self._json({"error": "session_not_found"}, 404)
            return self._json({"id": session_id, "items": session["ingredients"],
                               "preview": summary(cooking_core.preview(session["ingredients"], INGREDIENTS, RECIPES, CONFIG)),
                               "result": session.get("result")})
        files = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}
        filename = files.get(url.path)
        if filename is None:
            return self._json({"error": "not_found"}, 404)
        body = (ROOT / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", {"index.html": "text/html", "app.js": "text/javascript", "style.css": "text/css"}[filename] + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length))
            if self.path == "/api/preview":
                return self._json(summary(cooking_core.preview(data["items"], INGREDIENTS, RECIPES, CONFIG)))
            if self.path == "/api/start":
                items = data["items"]
                if not items:
                    raise ValueError("Choose at least one ingredient")
                cooking_core.aggregate(items, INGREDIENTS)
                session_id = uuid.uuid4().hex
                SESSIONS[session_id] = {"id": session_id, "ingredients": items, "saved_random": {}}
                SAVE.write_text(json.dumps(SESSIONS, ensure_ascii=False, indent=2), encoding="utf-8")
                return self._json({"id": session_id})
            if self.path == "/api/cook":
                session = SESSIONS.get(data["id"])
                if session is None:
                    return self._json({"error": "session_not_found"}, 404)
                sides = [int(value) for value in data["dice_sides"]]
                if any(side < 2 or side > 100 for side in sides):
                    raise ValueError("Die sides must be 2–100")
                result = cooking_core.cook(session, sides, int(data["cooking_level"]),
                                           energy=int(data["energy"]), ingredients=INGREDIENTS,
                                           recipes=RECIPES, config=CONFIG)
                SAVE.write_text(json.dumps(SESSIONS, ensure_ascii=False, indent=2), encoding="utf-8")
                return self._json(result)
            return self._json({"error": "not_found"}, 404)
        except (ValueError, KeyError, TypeError) as exc:
            return self._json({"error": str(exc)}, 400)


if __name__ == "__main__":
    address = ("127.0.0.1", 8765)
    print("ReMemorial cooking: http://%s:%s" % address)
    HTTPServer(address, Handler).serve_forever()
