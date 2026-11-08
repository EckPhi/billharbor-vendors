"""In-process invented portal implementing the seven browser-rpc/1 operations.

This is not a browser and opens no network connection. It models an invented
DOM (packaged ``data/fixture.json``) so offline conformance and tests exercise
exactly the operations the broker-owned browser offers: ``navigate``, ``fill``,
``click``, ``text``, ``attribute``, ``count`` and ``download``. Like the broker,
selectors are strict for single-element operations and any failure makes the
capability unusable for the rest of the execution.
"""
from __future__ import annotations

import copy
import json
import re
from importlib.resources import files
from urllib.parse import urlsplit

FIXTURE_VERSION = "oekostrom-invented-dom/1"
MAXIMUM_FIXTURE_BYTES = 1024 * 1024
_COMPOUND = re.compile(
    r'(?P<tag>[a-z][a-z0-9-]*)?(?P<rest>(?:#[A-Za-z0-9_-]+|\.[A-Za-z0-9_-]+'
    r'|\[[A-Za-z_][A-Za-z0-9_.:-]*(?:="[^"\\]*")?\])*)')
_PART = re.compile(r'#([A-Za-z0-9_-]+)|\.([A-Za-z0-9_-]+)|\[([A-Za-z_][A-Za-z0-9_.:-]*)(?:="([^"\\]*)")?\]')
_NTH = re.compile(r'nth=(0|[1-9][0-9]{0,5})')


class BrowserOperationFailed(RuntimeError):
    """Mirrors the broker's generic, value-free failure."""

    def __init__(self):
        super().__init__("Browser operation failed.")


def load_fixture():
    raw = files("oekostrom_at").joinpath("data/fixture.json").read_bytes()
    if len(raw) > MAXIMUM_FIXTURE_BYTES:
        raise ValueError("Invented portal fixture exceeds its bound")
    fixture = json.loads(raw)
    if (fixture.get("synthetic") is not True or fixture.get("connector_id") != "oekostrom_at"
            or fixture.get("fixture_version") != FIXTURE_VERSION):
        raise ValueError("Only the explicitly invented portal fixture is supported")
    return fixture


def _matches(element, simple):
    match = _COMPOUND.fullmatch(simple)
    if not match or (not match["tag"] and not match["rest"]):
        raise BrowserOperationFailed()
    attributes = element.get("attributes", {})
    if match["tag"] and element.get("tag") != match["tag"]:
        return False
    for identifier, cls, name, value in _PART.findall(match["rest"]):
        if identifier and attributes.get("id") != identifier:
            return False
        if cls and cls not in attributes.get("class", "").split():
            return False
        if name and (name not in attributes or (value and attributes[name] != value)):
            return False
    return True


def _descendants(element):
    for child in element.get("children", ()):
        yield child
        yield from _descendants(child)


class InventedPortal:
    """Invented portal state behind ``await portal(operation, **arguments)``."""

    def __init__(self, fixture, origin, *, credentials=None):
        if urlsplit(origin).hostname is None or not urlsplit(origin).hostname.endswith(".test"):
            raise ValueError("Invented portal requires a .test origin")
        self.origin = origin
        self.views = copy.deepcopy(fixture["views"])
        self.routes = dict(fixture["routes"])
        self.originals = {key: value.encode("ascii") for key, value in fixture["originals"].items()}
        self.authenticated = fixture.get("session") == "authenticated"
        self.challenge = False
        self.challenge_after_sign_in = False
        self.captcha = False
        self.credentials = credentials
        self.view = None
        self.failed = False
        self.filled = {}
        self.operations = []
        self.navigations = []
        self.downloads = []

    def _fail(self):
        self.failed = True
        raise BrowserOperationFailed()

    def _resolve(self, selector):
        if type(selector) is not str or not selector or re.search(r'(^|>>)\s*(javascript|js)\s*=', selector, re.I):
            self._fail()
        current = [{"children": self.views.get(self.view, [])}]
        for part in (piece.strip() for piece in selector.split(">>")):
            nth = _NTH.fullmatch(part)
            if nth:
                index = int(nth.group(1))
                current = [current[index]] if index < len(current) else []
                continue
            found, seen = [], set()
            for element in current:
                for candidate in _descendants(element):
                    if id(candidate) not in seen and _matches(candidate, part):
                        seen.add(id(candidate))
                        found.append(candidate)
            current = found
        return current

    def _single(self, selector):
        elements = self._resolve(selector)
        if len(elements) != 1:
            self._fail()  # Playwright locator operations are strict.
        return elements[0]

    def _route(self, path):
        # A CAPTCHA may interrupt either the sign-in form or an existing session.
        if self.captcha:
            return "captcha"
        if not self.authenticated:
            return "sign_in"
        if self.challenge:
            return "challenge"
        return self.routes[path]

    async def __call__(self, operation, **arguments):
        if self.failed:
            raise BrowserOperationFailed()
        self.operations.append((operation, arguments.get("selector", arguments.get("url"))))
        try:
            if operation == "navigate" and set(arguments) == {"url"}:
                parsed = urlsplit(arguments["url"])
                # Models the gateway: only the exact invented origin, no redirects.
                if (f"{parsed.scheme}://{parsed.netloc}" != self.origin or parsed.query
                        or parsed.fragment or parsed.path not in self.routes):
                    self._fail()
                self.navigations.append(arguments["url"])
                self.view = self._route(parsed.path)
                return None
            if operation == "count" and set(arguments) == {"selector"}:
                return len(self._resolve(arguments["selector"]))
            if operation == "text" and set(arguments) == {"selector"}:
                return self._single(arguments["selector"]).get("text", "")
            if operation == "attribute" and set(arguments) == {"selector", "name"}:
                return self._single(arguments["selector"]).get("attributes", {}).get(arguments["name"])
            if operation == "fill" and set(arguments) == {"selector", "value"}:
                element = self._single(arguments["selector"])
                if element.get("tag") != "input" or type(arguments["value"]) is not str:
                    self._fail()
                self.filled[element["attributes"]["name"]] = arguments["value"]
                return None
            if operation == "click" and set(arguments) == {"selector"}:
                element = self._single(arguments["selector"])
                if element.get("action") == "sign_in":
                    supplied = (self.filled.get("invented-user"), self.filled.get("invented-secret"))
                    self.filled.clear()
                    if self.credentials is not None and supplied == self.credentials:
                        self.authenticated = True
                        self.challenge = self.challenge_after_sign_in
                    self.view = self._route("/anmelden")
                return None
            if operation == "download" and set(arguments) == {"selector"}:
                element = self._single(arguments["selector"])
                if "original" not in element:
                    self._fail()
                self.downloads.append(element["original"])
                return self.originals[element["original"]]
        except BrowserOperationFailed:
            raise
        except Exception:
            self._fail()
        self._fail()

    # Test helpers modelling portal drift; never used by the connector.
    def rows(self, view="documents"):
        return [element for root in self.views[view] for element in (root, *_descendants(root))
                if _matches(element, "tr.invented-document")]

    def view_root(self, name="documents"):
        return self.views[name][0]
