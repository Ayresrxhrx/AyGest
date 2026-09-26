from __future__ import annotations
import sys
from pathlib import Path
PACKAGE_ROOT=Path(__file__).resolve().parent
PROJECT_ROOT=PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
from aygest_desktop.app import Database
from aygest_desktop.professional_app import ProfessionalApp
from aygest_desktop.login_ui import LoginWindow

def main()->None:
    db=Database(); tenant_id=db.bootstrap(); user=db.conn.execute('SELECT * FROM users WHERE tenant_id=? AND active=1 ORDER BY role LIMIT 1',(tenant_id,)).fetchone()
    app=ProfessionalApp(db,tenant_id,user); app.withdraw()
    def authenticated(auth_user):
        app.user=auth_user; app.user_id=auth_user['id']; app.deiconify(); app.open('Dashboard')
    app.withdraw(); LoginWindow(app,db,tenant_id,authenticated); app.mainloop()
if __name__=='__main__': main()
