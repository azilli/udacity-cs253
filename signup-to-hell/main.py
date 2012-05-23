#!/usr/bin/env python

import webapp2, sys
import hashlib
import random
import string
from validation import *

from google.appengine.ext import db

signup = open("htmls/signup.html", "r")
form = signup.read()
login = open("htmls/login.html", "r")
login_form = login.read()

def get_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def hash_str(name, pw, salt=None):
    if salt is None:
        salt = get_salt()
    return hashlib.sha256(name+pw+salt).hexdigest(), salt
    
#def make_secure_val(name, pw):
#    return "%s|%s" % (name, hash_str(name, pw))
        
class User(db.Model):
    name = db.StringProperty(required = True)
    hpw = db.StringProperty(required = True)
    salt = db.StringProperty(required = True)
    
    email = db.StringProperty()

class MainHandler(webapp2.RequestHandler):
    def view_form(self, username="", usr_err="", pswd_err="", ver_err="", email="", email_err=""):
        self.response.out.write(form % {'username':username,
                                        'username_error':usr_err,
                                        'password_error':pswd_err,
                                        'verify_error':ver_err,
                                        'email':email,
                                        'email_error':email_err})

    def get(self):
        self.view_form()
        
    def post(self):
        user_username = self.request.get('username')
        user_pswd = self.request.get('password')
        user_ver = self.request.get('verify')
        user_email = self.request.get('email')
        
        v_err = valid(user_username, user_pswd, user_ver, user_email)
        
        if not v_err or v_err['usr_err'] == "":
            us = db.GqlQuery(" SELECT * FROM User "
                             " WHERE name = :1", user_username)
            if len(us.fetch(1)) > 0:
                if v_err is None:
                    v_err = {'usr_err':"", 'pswd_err':"", 'v_err':"", 'e_err':""}
                v_err['usr_err'] = 'That user already exists.'
        
        if v_err is not None:
            self.view_form(user_username, v_err['usr_err'], v_err['pswd_err'], v_err['v_err'], user_email, v_err['e_err'])
        else:
            uhash = hash_str(user_username, user_pswd)
            u = User(name=user_username, email=user_email, salt=uhash[1], hpw=uhash[0])
            u.put()
            usr_cookie = str(u.key().id())+'|'+uhash[0]
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % usr_cookie)
            self.redirect('/signup/welcome')
            
class LogoutHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect('/signup')
            
class LoginHandler(webapp2.RequestHandler):
    def view_form(self, error=""):
        self.response.out.write(login_form % {'error':error} )

    def get(self):
        self.view_form()
    
    def post(self):
        user_username = self.request.get('username')
        user_pswd = self.request.get('password')
        
        if valid(user_username, user_pswd, user_pswd, "") is None:
            us = db.GqlQuery(" SELECT * FROM User "
                             " WHERE name = :1", user_username)
            for u in us:
                if u.hpw == hash_str(u.name, user_pswd, u.salt)[0]:
                    usr_cookie = str(u.key().id())+'|'+u.hpw
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(usr_cookie))
                    self.redirect('/signup/welcome')
                    return
        
        self.view_form("Invalid login")
        
                                
class WelcomeHandler(webapp2.RequestHandler):
    def check_secure_val(self, cookie):
        [usr_id, uhash] = cookie.split('|')
        if uhash:
            u = User.get_by_id(int(usr_id))
            if u.hpw == uhash:
                return True, u.name
        return False, ""   

    def get(self):
        user_cookie_str = self.request.cookies.get('user_id')
        #print user_cookie_str
        if user_cookie_str:
            cookie_val = self.check_secure_val(user_cookie_str)
            if cookie_val[0]:
                self.response.headers['Content-Type'] = 'text/html'
                self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(user_cookie_str))
                self.response.out.write("<h2>Welcome, %s!</h2>" % str(cookie_val[1]))        
                return
        #print "redirecting"
        self.redirect('/signup')

app = webapp2.WSGIApplication([('/signup', MainHandler),
                               ('/signup/welcome', WelcomeHandler),
                               ('/login', LoginHandler),
                               ('/logout', LogoutHandler)],
                              debug=True)
