from flask import Flask, render_template, Response, url_for, request, jsonify
import json, os, os.path
import random
from StringIO import StringIO
from passlib.apps import custom_app_context as passwords

app = Flask(__name__)

TURN_MESSAGE = "Turn is open"
projects = {}

class Project(object):
	def __init__(self, name):
		self.msgs   = []
		self.turnu  = None
		self.hash = None
		#self.code  = "Just type HTML..."
		self.name   = name
		self.msgid  = 1
		self.tokens = {}
		#self.online = []
		self.files  = {"index.html":"Just type HTML..."}
		
def to_json(proj):
	r = {}
	r['name']  = proj.name
	r['msgs']  = proj.msgs
	r['msgid'] = proj.msgid
	r['files'] = proj.files
	r['hash']  = proj.hash
	return json.dumps(r)
	
def from_json(str):
	pd      = json.loads(str)
	r       = Project(pd['name'])
	r.msgs  = pd['msgs']
	r.msgid = pd['msgid']
	r.files = pd['files']
	r.hash  = pd['hash']
	return r
	
def save_file(name, proj):
	path = '{}.json'.format(name)
	lastslash = path.rfind(os.pathsep)
	#npath                = os.path.join("data", path[lastslash:-1])
	if lastslash == -1:
		npath = "data/" + path
	else:
		npath = "data/" + path[lastslash:]
	
	print(npath)
	
	with open(npath, 'w') as f:
		f.write(to_json(proj))

@app.route("/")
def welcome():
	bootstrapcss = url_for('static', filename='bootstrap/css/bootstrap.min.css')
	return render_template('welcome.html')

@app.route("/project/<name>")
def index(name):
	if not name in projects:
		projects[name] = Project(name)
	return render_template('index.html', startf="index.html", project=name, turnopen=TURN_MESSAGE)


# disabled userlist code #
	
"""
@app.route("/project/<name>/users/add")
def adduser(name):
	proj = projects[name]
	u = request.args.get("u", None)
	if not u is None:
		proj.online.append(u)
		return "true"
	return "false"
		
@app.route("/project/<name>/users/remove")
def deluser(name):
	proj = projects[name]
	u = request.args.get("u", "")
	proj.online.remove(u)
	return "true"
"""

def rand_token():
	symbols = ["@", "*", "&", "%", "#", "$"]
	letters = ["1", "2", "0", "4", "A", "B", "C", "D", "E", "F"]
	r = ""
	for _ in range(random.randint(2, 5)):
		for _ in range(random.randint(5,10)):
			r += random.choice(symbols)
		for _ in range(random.randint(5,10)):
			r += random.choice(letters)
	return passwords.encrypt(r)

def check_password(name, pw, user):
	proj = projects[name]
	if passwords.verify(pw, proj.hash):
		token = rand_token()
		proj.tokens[user] = token
		return token
	else:
		return "false"
		
def check_token(name, pw, user):
	proj = projects[name]
	if proj.tokens[user] == pw:
		return "true"
	else:
		return "false"

@app.route("/project/<name>/password")
def check_pass_login(name):
	proj = projects[name]
	pw = request.args.get("pw")
	user = request.args.get("user")
	return check_password(name, pw, user)

@app.route("/project/<name>/password/set")
def set_password(name):
	proj = projects[name]
	user = request.args.get("user")
	if proj.hash is None:
		hash = passwords.encrypt(request.args.get("pw"))
		proj.hash = hash
		proj.tokens[user] = rand_token()
		return proj.tokens[user]
	else:
		return "false"
		
@app.route("/project/<name>/password/which")
def elgible(name):
	proj = projects[name]
	print proj.hash
	if proj.hash is None:
		return "true"
	else:
		return "false"

@app.route("/view/<name>/<filename>")
def view(name, filename):
	proj = projects[name]
	if filename.endswith(".html"):
		if filename in proj.files:
			return render_template('view.html', code=proj.files[filename])
		else:
			return "<h1>404 Not Found</h1>"
	else:
		return Response(proj.files[filename], mimetype='text/css')

@app.route("/project/<name>/render/<fname>")
def render(name, fname):
	proj = projects[name]
	if fname.endswith(".html"):
		return render_template('render.html', html=True, project=proj.name, fname=fname)
	else:
		return Response(proj.files[fname], mimetype='text/css')

@app.route("/project/<name>/files/create")
def create_file(name):
	proj = projects[name]
	pw = request.args.get("pw")
	user = request.args.get("user")
	fname = request.args.get("filename")
	if not check_token(name, pw, user) == "false":
		if fname.endswith(".html"):
			proj.files[request.args.get('filename')] = 'Just type HTML...'
		else:
			proj.files[request.args.get('filename')] = 'Just type CSS...'
		save_file(name, proj)
		return "true"
	else:
		print "HACKARR!"
		return "false"
		
@app.route("/project/<name>/files/delete")
def delete_file(name):
	proj = projects[name]
	pw = request.args.get("pw")
	user = request.args.get("user")
	fname = request.args.get("filename")
	if not check_token(name, pw, user) == "false":
		del proj.files[fname]
		return "true"
	else:
		print "HACKARR!"
		return "false"
	
@app.route("/project/<name>/msgs/send", methods=['POST'])
def newmessage(name):
	pw = request.form["pw"]
	proj = projects[name]
	user = request.form["user"]
	if not check_token(name, pw, user) == "false":
		proj.msgs.append([proj.msgid,request.form['message']])
		proj.msgid += 1
		return "true"
	else:
		print "HACKARR!"
		return "false"

@app.route("/project/<name>/msgs/check")
def check(name):
	pw = request.args.get("pw")
	proj = projects[name]
	user = request.args.get("user")
	if not check_token(name, pw, user) == "false":
		lastid = int(request.args.get("lastid", "null")) #return null as default so it cannot be converted to an int
		#print proj.msgs
		print lastid
		print proj.msgid
		if lastid != proj.msgid:
			return jsonify(proj.msgs[lastid:proj.msgid])
		return jsonify([])
	else:
		return jsonify([])
		
@app.route("/project/<name>/msgs/clear")
def clearmsgs(name):
	pw = request.args.get("pw")
	proj = projects[name]
	user = request.args.get("user")
	if not check_token(name, pw, user) == "false":
		proj.msgs = []
		proj.msgid = 1
		return "True"
	else:
		return "False"
		
@app.route("/project/<name>/code/send")
def send_code(name):
	filename = request.args.get("filename")
	pw = request.args.get("pw")
	proj = projects[name]
	user = request.args.get("user")
	if not check_token(name, pw, user) == "false":
		proj.files[filename] = request.args.get("code")
		print request.args.get("code")
		save_file(name, proj)
		return "true"
	else:
		return "false"

@app.route("/project/<name>/code/get")
def get_code(name):
	filename = request.args.get("filename", "index.html")
	proj = projects[name]
	if filename in proj.files:
		return proj.files[filename]
	else:
		return "<h1>" + filename + "</h1><p>This file has been deleted</p>"

@app.route("/project/<name>/files/list")
def get_files(name):
	pw = request.args.get("pw")
	proj = projects[name]
	user = request.args.get("user")
	return render_template("fileslist.html", files=proj.files, USERNAME=user, TOKEN=pw)
	
@app.route("/project/<name>/turns/start", methods=['POST'])
def start_turn(name):
	proj = projects[name]
	pw = request.form["pw"]
	user = request.form["user"]
	if not check_token(name, pw, user) == "false":
		if proj.turnu is None:
			proj.turnu = request.form['name']
			return "true"
		else:
			return "false"
	else:
		return "false"
		
@app.route("/project/<name>/turns/end")
def end_turn(name):
	proj = projects[name]
	user = request.args.get("user")
	pw = request.args.get("pw")
	if not check_token(name, pw, user) == "false":
		if request.args.get("name", "?") == proj.turnu:
			proj.turnu = None
			return "true"
		else:
			return "false"
	else:
		return "false"
	
@app.route("/project/<name>/turns/check")
def who_turn(name):
	proj = projects[name]
	if proj.turnu is None:
		return TURN_MESSAGE
	else:
		return proj.turnu + " is having a turn"
	
if __name__ == "__main__":
	for root, _, projs in os.walk("data/"):
		for p in projs:
			if not p.endswith(".json"):
				continue
			p = "data/" + p
			with open(p, 'r') as f:
				f = f.read()
				f = from_json(f)
				projects[f.name] = f
	app.run(host='0.0.0.0', debug=True)