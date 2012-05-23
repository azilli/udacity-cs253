#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os, json, sys
import hashlib
import random
import string
from validation import *

import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

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
            
def date(p):
    return p.created.strftime("%a %b %d %H:%M:%S %Y")

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
        
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
        
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        
class Post(db.Model):
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
        
class User(db.Model):
    name = db.StringProperty(required = True)
    hpw = db.StringProperty(required = True)
    salt = db.StringProperty(required = True)
    
    email = db.StringProperty()
        
class MainPage(Handler):
    def render_front(self):
        posts = db.GqlQuery("SELECT * FROM Post "
                           "ORDER BY created DESC ")
        self.render("front.html", posts=posts)

    def get(self):
        self.render_front()
        
class ViewEntry(Handler):
    def get(self, post_id):
        p = Post.get_by_id(int(post_id))
        if p:
            self.render("front.html", posts=[p])
            
class JsonResponse(Handler):
    def get(self, post_id=None):
        self.response.headers['Content-Type'] = 'application/json'
        if post_id:
#            post_id = post_id[1:]
            p = Post.get_by_id(int(post_id))
            if p:            
                self.response.out.write(str(json.dumps({"content":p.title, "created":date(p), "last_modified":date(p), "subject":p.content})))
        else:
            l = []
            posts = db.GqlQuery("SELECT * FROM Post "
                           "ORDER BY created DESC ")
            for p in posts:
                l.append({"content":p.title, "created":date(p), "last_modified":date(p), "subject":p.content})
            self.response.out.write(str(json.dumps(l)))
        
class NewEntry(Handler):
    def render_new(self, title="", content="", error=""):
        self.render("newpost.html", title=title, content=content, error=error)
        
    def get(self):
        self.render_new()
        
    def post(self):
        title = self.request.get("subject")
        content = self.request.get("content")
        
        if title and content:
            p = Post(title=title, content=content)
            p.put()
            
            self.redirect("/%s" % str(p.key().id()))
        else:
            error = "we need both a title and some content!"
            self.render_new(title, content, error)

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
            self.redirect('/welcome')
            
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
                    self.redirect('/welcome')
                    return
        
        self.view_form("Invalid login")
        
                                
class WelcomeHandler(webapp2.RequestHandler):
    def check_secure_val(self, cookie):
        [usr_id, uhash] = cookie.split('|')
       # print usr_id, uhash
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


app = webapp2.WSGIApplication([('/', MainPage), ('/newpost', NewEntry), ('/([0-9]+)', ViewEntry), ('/([0-9]+)?\.json', JsonResponse), ('/signup', MainHandler), ('/welcome', WelcomeHandler), ('/login', LoginHandler), ('/logout', LogoutHandler)],
                              debug=True)
