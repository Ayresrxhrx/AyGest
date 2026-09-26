from __future__ import annotations

import sys
from pathlib import Path

# Allow PyInstaller to execute this module as a top-level script while
# retaining package imports when launched with `python -m`.
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aygest_desktop.app import App
from aygest_desktop.login_ui import LoginWindow


def main() -> None:
    app = App()
    app.withdraw()

    def authenticated(user):
        app.user = user
        app.user_id = user['id']
        app.deiconify()
        app._shell()

    LoginWindow(app, app.db, app.tenant_id, authenticated)
    app.mainloop()


if __name__ == '__main__':
    main()
