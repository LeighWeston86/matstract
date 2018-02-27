from dash_auth.auth import Auth
import base64
import flask


class UserAuth(Auth):
    def __init__(self, app, user_list):
        Auth.__init__(self, app)
        self._user_list = user_list
        self.username = ""

    def is_authorized(self):
        header = flask.request.headers.get('Authorization', None)
        if not header:
            return False
        username_password = base64.b64decode(header.split('Basic ')[1])
        username_password_utf8 = username_password.decode('utf-8')
        username, password = username_password_utf8.split(':')
        for pair in self._user_list:
            if pair[0] == username and pair[1] == password:
                self.username = username
                return True

        return False

    def login_request(self):
        return flask.Response(
            'Login Required',
            headers={'WWW-Authenticate': 'Basic realm="Use your full name and the not encrypted password!"'},
            status=401)

    def auth_wrapper(self, f):
        def wrap(*args, **kwargs):
            if not self.is_authorized():
                return flask.Response(status=403)

            response = f(*args, **kwargs)
            return response
        return wrap

    @staticmethod
    def authenticate(dash_app, db):
        users = db.users.find({})
        user_list = []
        for user in users:
            user_list.append([user["username"], user["password"]])
        return UserAuth(dash_app, user_list)
