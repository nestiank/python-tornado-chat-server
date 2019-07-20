from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.web import Application, RequestHandler, url, StaticFileHandler
import time
import pickle
import signal, logging, os
class FastStop:
    def __init__(self):
        self.is_closing = False
    def enable(self):
        def signal_handler(signum, frame):
            self.is_closing = True
        def try_exit():
            if self.is_closing:
                IOLoop.instance().stop()
        signal.signal(signal.SIGINT, signal_handler)
        PeriodicCallback(try_exit, 100).start()

history = []
member = []
session = []

class MainHandler(RequestHandler):
    def get(self):
        self.render('main.html')

class JoinHandler(RequestHandler):
    def post(self):
        global history
        user_id = self.get_body_argument('user_id')
        user_pw = self.get_body_argument('user_pw')
        login_info = {'user_id': user_id, 'user_pw': user_pw}
        if login_info in member:
            global session
            session.append(login_info)
            self.render('join.html', user_id=user_id, history=history)
        else:
            self.render('error_login.html')

class RegisterHandler(RequestHandler):
    def post(self):
        user_id = self.get_body_argument('user_id')
        user_pwin = self.get_body_argument('user_pwin')
        user_pwrp = self.get_body_argument('user_pwrp')
        if user_pwin == user_pwrp and user_id != "" and user_pwin != "":
            global member
            user = {'user_id': user_id, 'user_pw': user_pwin}
            member.append(user)
            self.render('confirm.html')
        else:
            self.render('error_register.html')
    def get(self):
        self.render('register.html')

class TalkHandler(RequestHandler):
    def post(self):
        global history
        user_id = self.get_body_argument('user_id')
        mesg = self.get_body_argument('mesg')
        ip = self.request.remote_ip
        data = {'user_id': user_id, 'mesg': mesg, 'time':time.asctime(), 'ip': ip}
        history.append(data)
        user_pw = next((item for item in session if item["user_id"] == user_id), None)['user_pw']
        login_info = {'user_id': user_id, 'user_pw': user_pw}
        if login_info in session:
            self.render('talk.html', user_id=user_id, history=history)

class AdminLoginHandler(RequestHandler):
    def post(self):
        global session
        admin_info = {'user_id': "keist99", 'user_pw': "pyprj"}
        user_id = self.get_body_argument('user_id')
        user_pw = self.get_body_argument('user_pw')
        if {'user_id': user_id, 'user_pw': user_pw} == admin_info:
            session.append(admin_info)
            self.render('admin.html', history=history, user_id="keist99")
        else:
            self.render('error_adminlogin.html')

class AdminHandler(RequestHandler):
    def get(self):
        admin_info = {'user_id': "keist99", 'user_pw': "pyprj"}
        if admin_info in session:
            self.render('admin.html', history=history, user_id="keist99")
        else:
            self.render('admin_login.html')
    def post(self):
        admin_info = {'user_id': "keist99", 'user_pw': "pyprj"}
        if admin_info in session:
            global history
            cmd = self.get_body_argument('cmd')
            if cmd == 'dump':
                f = open('talk.hist', 'wb')
                pickle.dump(history,f)
                f.close()
            elif cmd == 'load':
                f = open('talk.hist', 'rb')
                history = pickle.load(f)
                f.close()
            self.render('admin.html', history=history, user_id="keist99")
        else:
            self.render('admin_login.html')

class LogoutHandler(RequestHandler):
    def post(self):
        global history
        user_id = self.get_body_argument('user_id')
        mesg = "(System) " + user_id + " left conversation."
        ip = self.request.remote_ip
        data = {'user_id': user_id, 'mesg': mesg, 'time':time.asctime(), 'ip': ip}
        history.append(data)
        user_pw = next((item for item in session if item["user_id"] == user_id), None)['user_pw']
        login_info = {'user_id': user_id, 'user_pw': user_pw}
        session.remove(login_info)
        self.render('logout.html', user_id=user_id)

class AdminLogoutHandler(RequestHandler):
    def post(self):
        global history
        user_id = self.get_body_argument('user_id')
        user_pw = next((item for item in session if item["user_id"] == user_id), None)['user_pw']
        login_info = {'user_id': user_id, 'user_pw': user_pw}
        session.remove(login_info)
        self.render('admin_logout.html', user_id=user_id)

def make_app():
    handlers = []
    handlers.append(url(r"/",MainHandler))
    handlers.append(url(r'/join',JoinHandler))
    handlers.append(url(r"/register",RegisterHandler))
    handlers.append(url(r'/talk',TalkHandler))
    handlers.append(url(r'/admin',AdminHandler))
    handlers.append(url(r'/admin_login',AdminLoginHandler))
    handlers.append(url(r'/logout',LogoutHandler))
    handlers.append(url(r'/admin_logout',AdminLogoutHandler))
    handlers.append(url(r"/files/(.*)", StaticFileHandler, {"path": os.path.dirname(os.path.abspath(__file__))}))
    return Application(handlers, static_path = os.path.join(os.path.dirname(__file__), "files"))

if __name__ == "__main__":
    fs = FastStop()
    fs.enable()
    app = make_app()
    app.listen(8080)
    IOLoop.current().start()