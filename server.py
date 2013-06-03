from flask import Flask, render_template, url_for, request, jsonify
import json, os, os.path
from StringIO import StringIO

app = Flask(__name__)

TURN_MESSAGE = "Turn is open"
projects = {}

class Project(object):
	def __init__(self, name):
		self.msgs   = []
		self.turnu  = None
		#self.code  = "Just type HTML..."
		self.name   = name
		self.msgid  = 1
		#self.online = []
		self.files  = {"index.html":"Just type HTML..."}
		
def to_json(proj):
	r = {}
	r['name']  = proj.name
	r['msgs']  = proj.msgs
	r['msgid'] = proj.msgid
	r['files']  = proj.files
	return json.dumps(r)
	
def from_json(str):
	pd      = json.loads(str)
	r       = Project(pd['name'])
	r.msgs  = pd['msgs']
	r.msgid = pd['msgid']
	r.files = pd['files']
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
	
@app.route("/view/<name>/<filename>")
def view(name, filename):
	return render_template('view.html', code=projects[name].files[filename])

@app.route("/project/<name>/render/<fname>")
def render(name, fname):
	proj = projects[name]
	return render_template('render.html', code=proj.files[fname], project=proj.name, fname=fname)

@app.route("/project/<name>/files/create")
def create_file(name):
	proj = projects[name]
	proj.files[request.args.get('filename')] = 'Just type HTML...'
	save_file(name, proj)
	return "true"
	
@app.route("/project/<name>/send", methods=['POST'])
def newmessage(name):
	proj = projects[name]
	proj.msgs.append([proj.msgid,request.form['message']])
	proj.msgid += 1
	return "Done"

@app.route("/project/<name>/check")
def check(name):
	proj = projects[name]
	lastid = int(request.args.get("lastid", "null")) #return null as default so it cannot be converted to an int
	#print proj.msgs
	if lastid != proj.msgid:
		return jsonify(proj.msgs[lastid:proj.msgid])
	return jsonify([])
		
@app.route("/project/<name>/code/send")
def send_code(name):
	filename = request.args.get("filename")
	proj = projects[name]
	proj.files[filename] = request.args.get("code", "<h1>Please Wait</h1>")
	
	save_file(name, proj)
	return "true"

@app.route("/project/<name>/code/get")
def get_code(name):
	filename = request.args.get("filename", "index.html")
	proj = projects[name]
	return proj.files[filename]

@app.route("/project/<name>/files/list")
def get_files(name):
	proj = projects[name]
	return render_template("fileslist.html", files=proj.files)
	
@app.route("/project/<name>/turns/start", methods=['POST'])
def start_turn(name):
	proj = projects[name]
	if proj.turnu is None:
		proj.turnu = request.form['name']
		return "true"
	else:
		return "false"
		
@app.route("/project/<name>/turns/end")
def end_turn(name):
	proj = projects[name]
	if request.args.get("name", "?") == proj.turnu:
		proj.turnu = None
		return "true"
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