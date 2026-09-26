from __future__ import annotations
from .app import App
from .login_ui import LoginWindow


def main():
    app=App()
    app.withdraw()
    def authenticated(user):
        app.user=user
        app.user_id=user['id']
        app.deiconify()
        app._shell()
    LoginWindow(app,app.db,app.tenant_id,authenticated)
    app.mainloop()

if __name__=='__main__': main()
