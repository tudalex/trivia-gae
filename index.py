import os
import cgi
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
import random
import logging

class Question(db.Model):
	question = db.StringProperty()
	answer = db.StringProperty()

class User_data(db.Model):
	user = db.UserProperty(auto_current_user=True)
	endurance = db.IntegerProperty()
	strength = db.FloatProperty()
	hitpoints = db.IntegerProperty()
	skill_mining = db.FloatProperty()
	skill_research = db.FloatProperty()
	skill_manufacturing = db.FloatProperty()
	skill_construction = db.FloatProperty()
	xp = db.IntegerProperty()
	level = db.IntegerProperty()
	luck = db.IntegerProperty()

#transaction functions
def IncreaseSkill(key, skill, bonus):
	key = db.Key.from_path('User_data',key)
	q = User_data.get(key)
	if not q:
		logging.error("User is not in database!!")
	if skill == "mining":
		q.skill_mining+=(1/float(long(q.skill_mining)+1))*bonus;
	if skill == "research":
		q.skill_research+=(1/float(long(q.skill_research)+1))*bonus;
	if skill == "manufacturing":
		q.skill_manufacturing+=(1/float(long(q.skill_manufacturing)+1))*bonus;
	if skill == "construction":
		q.skill_construction+=(1/float(long(q.skill_construction)+1))*bonus;
	q.put()

def IncreaseXP(points):
	user = users.get_current_user()
	q = User_data.get(db.Key.from_path('User_data', user.user_id()))
	q.xp+=points;
	q.put()
	
class MainPage(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			data = User_data.get_or_insert(user.user_id(), hitpoints = 100, strength=1.0, skill_mining=0.0, skill_research = 0.0, skill_construction=0.0, skill_manufacturing=0.0, xp = 0, level = 1)
			
			
			template_values = { 'skill_mining': data.skill_mining, 'skill_research':data.skill_research, 'skill_construction':data.skill_construction, 'skill_manufacturing': data.skill_manufacturing, 'xp': data.xp, 'level': data.level }
			
			path = os.path.join(os.path.dirname(__file__),'dashboard.html')
			
			self.response.out.write(template.render(path,template_values))
		else:
			self.redirect(users.create_login_url("/"))

class Work(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user is None:
			self.redirect(users.create_login_url("/"))
		
		self.response.out.write('''
		<html>
			<body>
				<form action="/work" method="post">
					<input type="radio" name="type" value="research" /> Reasarch<br />
					<input type="radio" name="type" value="mining" /> Mining<br />
					<input type="radio" name="type" value="construction" /> Construction<br />
					<input type="radio" name="type" value="manufacturing" /> Manufacturing <br />
					<input type="submit" value="Work">
				</form>
			</body>
		</html>''')
	def post(self):
		user = users.get_current_user()
		if self.request.get('challenge_id'):
			ok = memcache.get(cgi.escape(self.request.get("challenge_id")))
			memcache.delete(cgi.escape(self.request.get("challenge_id")))
			if ok is not None:
				if ok.answer == self.request.get("answer"):
					db.run_in_transaction(IncreaseSkill, user.user_id(), self.request.get('type'), 1)
					db.run_in_transaction(IncreaseXP, 10)
			self.redirect('/')
		else:
			q=Question.all()
			questions = q.fetch(1000)
			#question = random.choice(data)
		
			q = User_data.get_or_insert(user.user_id(), points=0)
			
			
		
		
			#We really need some optimizations for this....fetching all the questions is...OVERKILL
			question = random.choice(questions)
			while True:
				challenge_id = random.randint(0,32768)
				if memcache.get("ch_"+str(challenge_id)) is None:
					memcache.set("ch_"+str(challenge_id), question,3660)
					break
			template_values = { 'question': question.question, 'challenge_id': "ch_"+str(challenge_id), 'type': cgi.escape(self.request.get('type')) }
			path = os.path.join(os.path.dirname(__file__),'trivia.html')
			self.response.out.write(template.render(path,template_values))

application = webapp.WSGIApplication(
                                     [('/', MainPage),('/work',Work)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
