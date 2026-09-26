from __future__ import annotations
import sys
from pathlib import Path
PACKAGE_ROOT=Path(__file__).resolve().parent
PROJECT_ROOT=PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
from aygest_desktop.pro_app import ProApp
from aygest_desktop.login_ui import LoginWindow

def main()->None:
    app=ProApp();app.withdraw()
    def authenticated(user):
        app.user=user;app.user_id=user['id'];app.deiconify();app._shell()
    LoginWindow(app,app.db,app.tenant_id,authenticated);app.mainloop()
if __name__=='__main__': main()
