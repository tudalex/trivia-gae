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
	question = db.TextProperty()
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
	points = db.IntegerProperty()




class MainPage(webapp.RequestHandler):
    def get(self):
    	user = users.get_current_user()
    	if user:
    		self.redirect("/play")
    	else:
    		self.redirect(users.create_login_url("/"))

def point_add(key, points):
	key = db.Key.from_path('User_data',key)
	q = User_data.get(key)
	if not q:
		q=User_data()
		q.points = 0
	q.points += points;
	q.put();

class Play(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user() #If we got here we should have a user...
		q=Question.all()
		questions = q.fetch(1000)
		#question = random.choice(data)
		
		q = User_data.get_or_insert(user.user_id(), points=0)
		points = q.points;
		if points is None:
			memcache.set("u"+user.user_id(), 0)
			points = 0
		
		
		#We really need some optimizations for this....fetching all the questions is...OVERKILL
		question = random.choice(questions)
		while True:
			challange_id = random.randint(0,32768)
			if memcache.get("ch_"+str(challange_id)) is None:
				memcache.set("ch_"+str(challange_id), question,3660)
				break
		template_values = { 'question': question.question, 'challange_id': "ch_"+str(challange_id), 'points': points}
		path = os.path.join(os.path.dirname(__file__),'trivia.html')
		self.response.out.write(template.render(path,template_values))
		
	def post(self):
		#Aici verificam raspunsurile si dam puncte
		user = users.get_current_user()
		#self.response.out.write("the answer was ")
		#self.response.out.write(cgi.escape(self.request.get("answer")))
		ok = memcache.get(cgi.escape(self.request.get("challenge_id")))
		if ok is not None:
			if ok.answer == self.request.get("answer"):
				db.run_in_transaction(point_add, user.user_id(), 10)
				
			#	self.response.out.write("<br> The answer was correct")
			
			#	self.response.out.write("<br> The answer was not correct")
		self.redirect('/play')


class Insert(webapp.RequestHandler):
	def get(self):
		self.response.out.write('''
		<html>
			<body>
				<form action="/insert" method="post">
					<label>Question:<textarea rows="5" cols="80" name="question"></textarea></label>
					<label>Answer:<input type="text" name="answer"></label>
					<input type="submit" value="Save question">
				</form>
			</body>
		</html>''')
	def post(self):
		question = Question()
		question.question=cgi.escape(self.request.get('question'))
		question.answer=cgi.escape(self.request.get('answer'))
		question.put()
		self.redirect("/insert")


application = webapp.WSGIApplication(
                                     [('/', MainPage),('/insert',Insert),('/play',Play)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
