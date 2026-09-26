from aygest_desktop.app_v2 import App
from aygest_desktop.login_ui import LoginWindow

if __name__=='__main__':
    app=App();app.withdraw()
    def authenticated(user):
        app.user=user;app.user_id=user['id'];app.deiconify();app._shell()
    LoginWindow(app,app.db,app.tenant_id,authenticated);app.mainloop()
