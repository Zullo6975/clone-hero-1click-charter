from __future__ import annotations

import requests
from packaging import version
from PySide6.QtCore import QObject, QThread, Signal

from charter import __version__

class UpdateChecker(QObject):
    update_available = Signal(str, str) # version_tag, url

    def check_github(self):
        url = "https://api.github.com/repos/zullo6975/clone-hero-1click-charter/releases/latest"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                tag = data.get("tag_name", "").strip()
                html_url = data.get("html_url", "")

                # Remove 'v' prefix if present for comparison
                clean_tag = tag.lstrip("v")

                if version.parse(clean_tag) > version.parse(__version__):
                    self.update_available.emit(tag, html_url)
        except Exception:
            pass # Fail silently if no internet

class UpdateWorker(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checker = UpdateChecker()

    def run(self):
        self.checker.check_github()
