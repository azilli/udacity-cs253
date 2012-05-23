import re

def valid(username, pswd, ver, email):
    errors = {'usr_err':"", 'pswd_err':"", 'v_err':"", 'e_err':""}
    if len(re.findall(r'^[a-zA-Z0-9_-]{3,20}$', username)) == 0:
        errors['usr_err'] = "That's not a valid username."
    if len(re.findall(r'^.{3,20}$', pswd)) == 0:
        errors['pswd_err'] = "That wasn't a valid password."
    if errors['pswd_err'] == "" and ver != pswd:
        errors['v_err'] = "Your passwords didn't match."
    if len(re.findall(r'^[\S]+@[\S]+\.[\S]+$', email)) == 0 and len(email)>0:
        errors['e_err'] = "That's not a valid email."
    if sum([len(er) for er in errors.values()]) == 0:
        return None
    return errors
