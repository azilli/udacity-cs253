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
import webapp2, cgi
from string import maketrans

rot13 = open("htmls/rot13.html", "r")
form = rot13.read()

a = "abcdefghijklmnopqrstuvwxyz"
b = "nopqrstuvwxyzabcdefghijklm"
a += a.upper()
b += b.upper()

rotate_table = maketrans(a, b)

def escape_html(s):
    return cgi.escape(s, quote = True)
    
def rotate(s):
    s = str(s)
    return s.translate(rotate_table)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.view_form()
        
    def view_form(self, text=""):
        self.response.out.write(form % {"text":escape_html(text)})
        
    def post(self):
        user_text = self.request.get('text')
        self.view_form(rotate(user_text))

app = webapp2.WSGIApplication([('/', MainHandler)],
                              debug=True)
