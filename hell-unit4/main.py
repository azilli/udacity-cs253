import os
import webapp2
import jinja2
import hashlib
import hmac

from google.appengine.ext import db

SECRET = 'imsosecret'

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def hash_str(s):
#    return hashlib.md5(s).hexdigest()
    return hmac.HMAC(SECRET, s).hexdigest()
    
def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))
    
def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
        
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        
class MainPage(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits = 0
        visit_cookie_str = self.request.cookies.get('visits')
        if visit_cookie_str:
            cookie_val = check_secure_val(visit_cookie_str)
            if cookie_val:
                visits = int(cookie_val)
                
        visits += 1
        
        new_cookie_val = make_secure_val(str(visits))
        
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % new_cookie_val)
        
        self.write("You've been here %s times!" % visits)
app = webapp2.WSGIApplication([('/', MainPage)], debug = True)
