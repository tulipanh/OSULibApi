import webapp2
import os
import sys
import datetime
import db_defs
from google.appengine.ext import ndb
import json
import mimetypes

class mainpage(webapp2.RequestHandler):
	def get(self):
		self.response.write("There's Nothing Here.")
		return

class people(webapp2.RequestHandler):
	def get(self):
		#Should return a JSON object containing all the emails of the people in the system
		query = db_defs.Person.query()
		people = query.fetch()
		result = []
		for x in people:
			result.append(x.key.id())
		self.response.write(json.dumps(result))
		return

	def post(self):
		#Should accept information for a new person and add the person to the database
		#If email is already in the system, return error
		#Otherwise should return a JSON object containing all the information of the person just created
		#How to do email verification (Apache modules?Regex?)
		if goodInput(self, {'fname': 'str', 'lname': 'str', 'email': 'email'}):
			pkey = ndb.Key('Person', self.request.get('email'))
			test = pkey.get()
			if not test:
				newperson = db_defs.Person()
				newperson.key = pkey
				newperson.fname = self.request.get('fname')
				newperson.lname = self.request.get('lname')
				#Authorization to be done later using webapp2 security features
				if self.request.get('privilege'):
					if goodInput(self, {'privilege': 'int'}):
						newperson.privilege = int(self.request.get('privilege'))
					else:
						return
				else:
					newperson.privilege = 1
				newperson.reviewables = []
				result = newperson.to_dict()
				result['email'] = newperson.key.id()
				newperson.put()
				self.response.write(json.dumps(result))
			else:
				errorMessage(self, 500, 'That email is already in use.')
		return

	def put(self):
		#Unsupported for this resource
		errorMessage(self, 300, 'That feature is unsupported at this time')
		return

	def delete(self):
		#Authorization to handled seperately using webapp2 security features
		query = db_defs.Person.query()
		for key in query.iter(keys_only=True):
			#Do I want to delete all children as well or simply alter them?
			#What to do with corresponding information stored in other entity groups?
			ndb.delete_multi(ndb.Query(ancestor=key).iter(keys_only=True))
			key.delete()

class person(webapp2.RequestHandler):
	def get(self, email):
		#Should return a JSON object containing the information of the person specified by the 
		person = getPerson(self, email)
		if person:
			result = person.to_dict()
			result['email'] = person.key.id()
			self.response.write(json.dumps(result))
		return

	def post(self, email):
		#Unsupported for this resource
		errorMessage(self, 300, 'That feature is unsupported at this time.')
		return

	def put(self, email):
		#Should update the information for the person specified by the email
		#Should return a JSON object containing the updated information
		#Perhaps I should write a function for this checking procedure.
		person = getPerson(self, email)
		if person:
			if self.request.get('fname'):
				person.fname = self.request.get('fname')
			if self.request.get('lname'):
				person.lname = self.request.get('lname')
			if self.request.get('privilege'):
				if not goodInput(self, {'privilege': 'int'}):
					return
				person.privilege = int(self.request.get('privilege'))
			if self.request.get('email'):
				errorMessage(self, 500, 'Cannot change email.')
			result = person.to_dict()
			result['email'] = person.key.id()
			person.put()
			self.response.write(json.dumps(result))
		return

	def delete(self, email):
		#Should delete the person from the database specified by the email.
		#Should delete all children of the person too? Reviews? Checkouts? 
		person = getPerson(self, email)
		if person:
			ndb.delete_multi(ndb.Query(ancestor=person.key).iter(keys_only=True))
			person.key.delete()
		return

#To be tested once books and checkouts have been checked
class personreviews(webapp2.RequestHandler):
	#Ended up storing reviews seperate from both Person and Book, querying to filter reviews by email and by book id
	def get(self, email):
		#Should return a JSON object containing all the reviews created by the person specified by the email
		#Maybe should just return the ids of all the reviews rather than all of the full review information.
		person = getPerson(self, email)
		if person:
			query = db_defs.Review.query(db_defs.Review.email == email)
			revs = query.fetch()
			results = []
			for x in revs:
				result = x.to_dict()
				result['ID'] = x.key.id()
				results.append(result)
			self.response.write(json.dumps(results))
		return

	def post(self, email):
		#Either unsupported or redirect to /reviews, or perhaps all reviews should be this way (through the person resource to check book id against the person's reviewable list?)
		person = getPerson(self, email)
		if person:
			if goodInput(self, {'bookid': 'int', 'text': 'text'}):
				book = getBook(self, self.request.get('bookid'))
				if book:
					if book.key.id() in person.reviewables:
						newrev = db_defs.Review()
						newrev.fname = person.fname
						newrev.bookid = book.key.id()
						newrev.title = book.title
						newrev.text = self.request.get('text')
						result = newrev.to_dict()
						newrev.put()
						self.response.write(json.dumps(result))
					else:
						errorMessage(self, 500, 'That user may not review that book.')
		return

	def put(self, email):
		#Unsupported
		errorMessage(self, 300, 'That feature is unsupported at this time.')
		return

	def delete(self, email):
		#Should delete all reviews created by the person specified by the email
		person = getPerson(self, email)
		if person:
			query = db_defs.Review.query(db_defs.Review.email == email)
			for key in query.iter(keys_only=True):
				key.delete()
		return

#To be tested once books and checkouts have been checked
class review(webapp2.RequestHandler):
	def get(self, rid):
		#Should return a JSON object containing all information about the review specified by the rid
		review = db_defs.Review.get_by_id(int(rid))
		if not review:
			errorMessage(self, 500, 'That review is not in the system.')
		else:
			result = review.to_dict()
			result['ID'] = int(rid)
			self.response.write(json.dumps(result))
		return

	def post(self, rid):
		#Unsupported
		errorMessage(self, 300, 'That feature is unsupported at this time.')
		return

	def put(self, rid):
		#Should update the information for the review specified by the rid
		#Should return a JSON object containing all the updated information
		review = db_defs.Review.get_by_id(int(rid))
		if not review:
			errorMessage(self, 500, 'That review is not in the system.')
		else:
			if self.request.get('text'):
				review.text = self.request.get('text')
				review.put()
			elif self.request.get('bookid') or self.request.get('email') or self.request.get('title') or self.request.get('fname'):
				errorMessage(self, 500, 'May only edit text of a review.')
		return

	def delete(self, rid):
		#Should delete the review specified by the rid
		review = db_defs.Review.get_by_id(int(rid))
		if not review:
			errorMessage(self, 500, 'That review is not in the system.')
		else:
			review.key.delete()
		return

#To be tested once books have been checked
class personcheckouts(webapp2.RequestHandler):
	def get(self, email):
		#Should return a JSON object containing all the checkouts associated with the person specified by the email
		person = getPerson(self, email)
		if person:
			query = db_defs.Checkout.query(ancestor=person.key)
			checkouts = query.fetch()
			for x in checkouts:
				result.append({'bookid': int(x.bookid), 'copyid': int(x.copyid), 'status': x.status, 'startdate': x.startdate, 'duedate': x.duedate, 'ID': x.key.id()})
			self.response.write(json.dumps(result))
		return

	def post(self, email):
		#Should create a new checkout with the information provided
		#Maybe should update the copy of the book specified as well or maybe this should be done through a separate API call to the copy itself
		if goodInput(self, ['bookid', 'copyid', 'length']):
			person = getPerson(self, email)
			book = getBook(self, self.request.get('bookid'))
			copy = getCopy(self, self.request.get('copyid'))
			if person and book and copy:
				if copy.status == 2:
					newco = db_defs.Checkout(parent=person.key)
					newco.bookid = book.key.id()
					newco.copyid = copy.key.id()
					newco.status = 1
					now = datetime.datetime.utcnow()
					due = now + datetime.datetime.timedelta(int(length))
					newco.startdate = now
					newco.duedate = due
					result = newco.to_dict()
					self.response.write(json.dumps(result))
					newco.put()
				elif copy.status == 1:
					errorMessage(self, 500, 'That copy has been returned, but is not yet available.')
				elif copy.status == 0:
					errorMessage(self, 500, 'That copy is currently checked out.')
		return

	def put(self, email):
		#Unsupported
		errorMessage(self, 300, 'That feature is unsuppored at this time.')
		return

	def delete(self, email):
		#Should remove all checkouts associated with the person specified by the email
		#Maybe should update the copies as well or maybe this should be done through separate API calls to the 
		person = getPerson(self, email)
		if person:
			query = db_defs.Checkout.query(ancestor=person.key)
			checkouts = query.fetch(keys_only=True)
			for x in checkouts:
				x.delete()
		return

#To be tested once books have been checked
class checkout(webapp2.RequestHandler):
	def get(self, chid):
		#Should return a JSON object containing all the information about the checkout specified by chid
		checkout = getCheckout(self, chid)
		if checkout:
			result = checkout.to_dict()
			result['ID'] = int(chid)
			self.response.write(json.dumps(result))
		return

	def post(self, chid):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsupported at this time.')
		return

	def put(self, chid):
		#Should update the checkout with the information provided
		#Should return a JSON object containing all the updated information
		checkout = getCheckout(self, chid)
		if checkout:
			if self.response.get('status'):
				checkout.status = self.response.get('status')
			if self.response.get('length'):
				due = checkout.duedate
				newdue = due + datetime.datetime.timedelta(int(length))
				checkout.duedate = newdue
			result = checkout.to_dict()
			result['ID'] = checkout.key.id()
			checkout.put()
			self.response.write(json.dumps(result))
		return

	def delete(self, chid):
		#Should remove the checkout associated with the chid
		#Maybe should update the copy as well or maybe should be done through a separate API call to the copy
		checkout = getCheckout(self, chid)
		if checkout:
			checkout.key.delete()
		return

#Still need to implement genrelist
class books(webapp2.RequestHandler):
	def get(self):
		#Should return a JSON object containing all the titles and book ids of the books in the database
		query = db_defs.Book.query()
		books = query.fetch()
		results = []
		for x in books:
			results.append({'ID': x.key.id(), 'title': x.title})
		self.response.write(json.dumps(results))
		return

	def post(self):
		#Should create a new book in the database
		#Should return all the information for the newly created
		#How should I do genre tags?
		if goodInput(self, {'title': 'str', 'edition': 'int', 'length': 'int', 'fname': 'str', 'lname': 'str', 'genres': 'str'}):
			book = db_defs.Book()
			book.title = self.request.get('title')
			book.edition = int(self.request.get('edition'))
			book.length = int(self.request.get('length'))
			book.genres = self.request.get('genres').split(',')
			author = db_defs.Author()
			author.fname = self.request.get('fname')
			author.lname = self.request.get('lname')
			book.author = author
			book.put()
			result = book.to_dict()
			result['ID'] = book.key.id()
			self.response.write(json.dumps(result))
		return

	def put(self):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsupported at this time.')
		return

	def delete(self):
		#Should remove all books in the database, should require a password of some kind, perhaps in the authorization header
		query = db_defs.Book.query()
		for key in query.iter(keys_only=True):
			#Do I want to delete all children as well or simply alter them?
			#What to do with corresponding information stored in other entity groups?
			ndb.delete_multi(ndb.Query(ancestor=key).iter(keys_only=True))
			key.delete()
			#Should it return any message?

class book(webapp2.RequestHandler):
	def get(self, bid):
		#Should return a JSON object containing all the information for the book specified by the bid
		book = getBook(self, bid)
		if book:
			result =  book.to_dict()
			result['ID'] = book.key.id()
			self.response.write(json.dumps(result))
		return

	def post(self, bid):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsupported at this time.')
		return

	def put(self, bid):
		#Should update the book specifed by the bid
		#Should return the updated information
		#How should I do genre tags?
		#Maybe should implement checking in db_defs for type and form of input?
		book = getBook(self, bid)
		if book:
			if self.request.get('title'):
				book.title = self.request.get('title')
			if self.request.get('length'):
				book.length = self.request.get('length')
			if self.request.get('edition'):
				book.edition = self.request.get('edition')
			if self.request.get('fname'):
				book.author.fname = self.request.get('fname')
			if self.request.get('lname'):
				book.author.lname = self.request.get('lname')
			result = book.to_dict()
			result['ID'] = book.key.id()
			result.put()
			self.response.write(json.dumps(result))
		return

	def delete(self, bid):
		#Should remove the book specified by the bid from the database
		book = getBook(self, bid)
		if book:
			ndb.delete_multi(ndb.Query(ancestor=book.key).iter(keys_only=True))
			book.key.delete()

class bookreviews(webapp2.RequestHandler):
	def get(self, bid):
		#Should return a JSON object containing all the reviews associated with the book specified by bid
		book = getBook(self, bid)
		if book:
			query = db_defs.Review.query(db_defs.Review.bookid == int(bid))
			reviews = query.fetch()
			results = []
			for x in reviews:
				result = x.to_dict()
				result['ID'] = x.key.id()
				results.append(result)
			self.response.write(json.dumps(results))
		return

	def post(self, bid):
		#Should create a new review for the book specified by the bid, or should be unsupported/handled by a different API call
		errorMessage(self, 500, 'This feature is unsupported at this time.')
		return

	def put(self, bid):
		#Unsupported
		errorMessage(self, 500, 'This feature is unsupported at this time.')
		return

	def delete(self, bid):
		#Should remove all reviews about the specified book
		book = getBook(self, bid)
		if book:
			query = db_defs.Review.query(db_defs.Review.bookid == int(bid))
			for key in query.iter(keys_only=True):
				key.delete()
		return

class bookcopies(webapp2.RequestHandler):
	def get(self, bid):
		#Should return a JSON object containing the information of all the copies of the specified book
		book = getBook(self, bid)
		if book:
			query = db_defs.Copy.query(ancestor=book.key)
			copies = query.fetch()
			results = {}
			for x in copies:
				result = x.to_dict()
				result['ID'] = x.key.id()
				results.append(result)
			self.response.write(json.dumps(results))
		return

	def post(self, bid):
		#Should create a new copy of the book in the database
		#Should return a JSON object containing the information of the newly created copy
		book = getBook(self, bid)
		if book:
			newcopy = db_defs.Copy(parent=book.key)
			newcopy.status = 2
			result = newcopy.to_dict()
			newcopy.put()
			self.response.write(json.dumps(result))
		return

	def put(self, bid):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsupported at this time.')
		return

	def delete(self, bid):
		#Should remove all the copies of the book specified by the bid
		book = getBook(self, bid)
		if book:
			query = db_defs.Copy.query(ancestor=book.key)
			for key in query.iter(keys_only=True):
				key.delete()
		return

class copy(webapp2.RequestHandler):
	def get(self, coid):
		#Should return a JSON object containing all the information associated with the specified copy
		copy = getCopy(self, coid)
		if copy:
			result = copy.to_dict()
			result['ID'] = copy.key.id()
			self.response.write(json.dumps(result))
		return

	def post(self, coid):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsuppoted at this time.')
		return

	def put(self, coid):
		#Should update the information for the copy specified by cid
		#Should return a JSON object containing all updated information
		#How to update history?
		copy = getCopy(self, coid)
		if copy:
			if self.request.get('status'):
				copy.status = self.request.get('status')
			result = copy.to_dict()
			result['ID'] = copy.key.id()
			self.response.write(json.dumps(result))
			copy.put()
		return

	def delete(self, coid):
		#Should remove from the database the copy specified by cid
		copy = getCopy(self, coid)
		if copy:
			copy.key.delete()
		return

class copyhistory(webapp2.RequestHandler):
	def get(self, coid):
		#Should return a JSON object containing a list of history entries (how are they ordered?)(do they need dates?)
		copy = getCopy(self, coid)
		if copy:
			history = copy.hisEntries
			result = []
			for entry in history:
				result.append(entry.to_dict())
			self.response.write(json.dumps(result))
		return

	def post(self, coid):
		#Should add a history entry to the history of the copy specified by coid
		copy = getCopy(self, coid)
		if copy and goodInput(self, ['email', 'duedate']):
			entry = db_defs.HisEntry()
			entry.email = self.request.get('email')
			entry.duedate = datetime.datetime.strptime(self.request.get('duedate'), '%Y-%m-%d')
			copy.hisEntries.append(entry)
			result = copy.to_dict()
			result['ID'] = copy.key.id()
			self.response.write(json.dumps(result))
			copy.put()
		return

	def put(self, coid):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsupported at this time.')
		return

	def delete(self, coid):
		#Should remove all history entries from the copy specified by coid
		copy = getCopy(self, coid)
		if copy:
			copy.hisEntries = []
			copy.put()
		return

def defaultResponse(handler):
	response = {}
	response['code'] = 100
	response['message'] = "This page has not yet been implemented."
	handler.response.write(json.dumps(response))
	return

def errorMessage(handler, code, message):
	response = {}
	response['code'] = code
	response['message'] = message
	handler.response.write(json.dumps(response))
	return

#Need to expand this function to check input types and forms
#Strings
#Ints
#Dates (Y-m-d)
#emails
#Could parse using regex, but regex is hard

def goodInput(handler, inputdict):
	for key in inputdict:
		if not handler.request.get(key):
			errorMessage(handler, 500, 'Required parameters not sent.')
			return False
		elif inputdict[key] == 'int':
			try:
				testint = int(handler.request.get(key))
			except:
				errorMessage(handler, 500, "Expected integer for input - %s" % key)
				return False
		elif inputdict[key] == 'str':
			try:
				teststr = str(handler.request.get(key))
			except:
				errorMessage(handler, 500, "Expected string for input - %s" % key)
				return False
		elif inputdict[key] == 'date':
			try:
				testdate = datetime.datetime.strptime(handler.request.get(key), '%Y-%m-%d')
			except:
				errorMessage(handler, 500, "Expected date for input - %s" % key)
				return False
		#elif inputdict[key] == 'email':
		#Email is hard to check for validity
	return True

def getPerson(handler, email):
	pkey = ndb.Key('Person', email)
	person = pkey.get()
	if not person:
		errorMessage(handler, 500, 'That person is not in the system.')
	return person

def getBook(handler, bid):
	bkey = ndb.Key('Book', int(bid))
	book = bkey.get()
	if not book:
		errorMessage(handler, 500, 'That book is not in the system.')
	return book

def getCopy(handler, coid):
	ckey = ndb.Key('Copy', int(coid))
	copy = ckey.get()
	if not copy:
		errorMessage(handler, 500, 'That copy is not in the system.')
	return copy 

def getCheckout(handler, chid):
	chkey = ndb.Key('Checkout', int(chid))
	checkout = chkey.get()
	if not checkout:
		errorMessage(handler, 500, 'That checkout is not in the system.')
	return checkout