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

#Deletion of a person should delete all children (checkouts) as well, without affecting the copies those checkouts correspond to.
#Deletion of a person should also remove all reviews associated with that person.
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
				if self.request.get('recentLat'):
					if goodInput(self, {'recentLat': 'float'}):
						newperson.recentLat = float(self.request.get('recentLat'))
					else:
						return
				if self.request.get('recentLong'):
					if goodINput(self, {'recentLong': 'float'}):
						newperson.recentLong = float(self.request.get('recentLong'))
					else:
						return
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
		errorMessage(self, 500, 'That feature is unsupported at this time')
		return

	def delete(self):
		#Authorization to handled seperately using webapp2 security features
		query = db_defs.Person.query()
		for key in query.iter(keys_only=True):
			#Delete all children
			ndb.delete_multi(ndb.Query(ancestor=key).iter(keys_only=True))
			#Delete all reviews
			rquery = db_defs.Review.query(db_defs.Review.email == key.id())
			for rkey in rquery.iter(keys_only=True):
				rkey.delete()
			key.delete()

class person(webapp2.RequestHandler):
	def get(self, email):
		#Should return a JSON object containing the information of the person specified by the email
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
			if self.request.get('recentLat'):
				if not goodInput(self, {'recentLat': 'float'}):
					return
				person.recentLat = float(self.request.get('recentLat'))
			if self.request.get('recentLong'):
				if not goodInput(self, {'recentLong': 'float'}):
					return
				person.recentLong = float(self.request.get('recentLong'))
			if self.request.get('email'):
				errorMessage(self, 500, 'Cannot change email.')
			result = person.to_dict()
			result['email'] = person.key.id()
			person.put()
			self.response.write(json.dumps(result))
		return

	def delete(self, email):
		person = getPerson(self, email)
		if person:
			ndb.delete_multi(ndb.Query(ancestor=person.key).iter(keys_only=True))
			rquery = db_defs.Review.query(db_defs.Review.email == person.key.id())
			for rkey in rquery.iter(keys_only=True):
				rkey.delete()
			person.key.delete()
		return

class personreviews(webapp2.RequestHandler):
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
		#All review should be created this way, so that the person's reviewables list can be checked.
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
						newrev.email = person.key.id()
						result = newrev.to_dict()
						newrev.put()
						result['ID'] = newrev.key.id()
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

class review(webapp2.RequestHandler):
	def get(self, rid):
		#Should return a JSON object containing all information about the review specified by the rid
		review = getReview(self, rid)
		if review:
			result = review.to_dict()
			result['ID'] = review.key.id()
			self.response.write(json.dumps(result))
		return

	def post(self, rid):
		#Unsupported
		errorMessage(self, 300, 'That feature is unsupported at this time.')
		return

	def put(self, rid):
		#Should update the information for the review specified by the rid
		#Should return a JSON object containing all the updated information
		review = getReview(self, rid)
		if review:
			if self.request.get('text'):
				if not goodInput(self, {'text': 'str'}):
					return
				review.text = self.request.get('text')
				review.put()
				result = review.to_dict()
				result['ID'] = review.key.id()
				self.response.write(json.dumps(result))
			elif self.request.get('bookid') or self.request.get('email') or self.request.get('title') or self.request.get('fname'):
				errorMessage(self, 500, 'May only edit text of a review.')
		return

	def delete(self, rid):
		#Should delete the review specified by the rid
		review = getReview(self, rid)
		if review:
			review.key.delete()
		return

#Needs to be tested again to see if checking out a book twice adds it twice to the reviewables list. (It Shouldn't)
class personcheckouts(webapp2.RequestHandler):
	def get(self, email):
		#Should return a JSON object containing all the checkouts associated with the person specified by the email
		person = getPerson(self, email)
		if person:
			checkouts = db_defs.Checkout.query(ancestor=person.key).fetch()
			results = []
			for x in checkouts:
				result = {}
				result = x.to_dict(exclude=['duedate', 'startdate'])
				result['startdate'] = datetime.datetime.strftime(x.startdate, "%Y-%m-%d")
				result['duedate'] = datetime.datetime.strftime(x.duedate, "%Y-%m-%d")
				result['ID'] = x.key.id()
				results.append(result)
			self.response.write(json.dumps(results))
		return

	def post(self, email):
		#Should create a new checkout with the information provided
		#Updates copy status to checked out. Does not revert it when deleted or updated. That must be done to the copy directly.
		if goodInput(self, {'bookid': 'int', 'copyid': 'int', 'length': 'int'}):
			person = getPerson(self, email)
			if not person:
				return
			book = getBook(self, self.request.get('bookid'))
			if not book:
				return
			copy = getCopy(self, self.request.get('bookid'), self.request.get('copyid'))
			if not copy:
				return
			if copy.status == 1:
				newco = db_defs.Checkout(parent=person.key)
				newco.bookid = book.key.id()
				newco.copyid = copy.key.id()
				newco.status = 1
				now = datetime.datetime.utcnow()
				due = now + datetime.timedelta(int(self.request.get('length')))
				newco.startdate = now
				newco.duedate = due
				newco.put()
				result = newco.to_dict(exclude=['duedate', 'startdate'])
				result['startdate'] = datetime.datetime.strftime(now, "%Y-%m-%d")
				result['duedate'] = datetime.datetime.strftime(due, "%Y-%m-%d")
				result['ID'] = newco.key.id()
				self.response.write(json.dumps(result))
				copy.status = 0
				entry = db_defs.HisEntry()
				entry.email = person.key.id()
				entry.startdate = now
				entry.chid = newco.key.id()
				copy.hisEntries.append(entry)
				copy.put()
				if book.key.id() not in person.reviewables:
					person.reviewables.append(book.key.id())
					person.put()
			elif copy.status == 1:
				errorMessage(self, 500, 'That copy has been returned, but is not yet available.')
			elif copy.status == 0:
				errorMessage(self, 500, 'That copy is currently checked out.')
		return

	def put(self, email):
		#Unsupported
		errorMessage(self, 300, 'That feature is unsupported at this time.')
		return

	def delete(self, email):
		#Should remove all checkouts associated with the person specified by the email
		person = getPerson(self, email)
		if person:
			query = db_defs.Checkout.query(ancestor=person.key)
			for x in query.iter(keys_only=True):
				x.delete()
		return

class checkout(webapp2.RequestHandler):
	def get(self, email, chid):
		#Should return a JSON object containing all the information about the checkout specified by chid
		checkout = getCheckout(self, email, chid)
		if checkout:
			result = checkout.to_dict(exclude=['duedate', 'startdate'])
			result['ID'] = int(chid)
			result['startdate'] = datetime.datetime.strftime(checkout.startdate, "%Y-%m-%d")
			result['duedate'] = datetime.datetime.strftime(checkout.duedate, "%Y-%m-%d")
			self.response.write(json.dumps(result))
		return

	def post(self, email, chid):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsupported at this time.')
		return

	def put(self, email, chid):
		#Should update the checkout with the information provided
		#Should return a JSON object containing all the updated information
		checkout = getCheckout(self, email, chid)
		if checkout:
			if self.request.get('status'):
				if not goodInput(self, {'status': 'int'}):
					return
				checkout.status = int(self.request.get('status'))
			if self.request.get('length'):
				if not goodInput(self, {'length': 'int'}):
					return
				due = checkout.duedate
				newdue = due + datetime.timedelta(int(self.request.get('length')))
				checkout.duedate = newdue
			result = checkout.to_dict(exclude=['duedate', 'startdate'])
			result['startdate'] = datetime.datetime.strftime(checkout.startdate, "%Y-%m-%d")
			result['duedate'] = datetime.datetime.strftime(checkout.duedate, "%Y-%m-%d")
			result['ID'] = checkout.key.id()
			checkout.put()
			self.response.write(json.dumps(result))
		return

	def delete(self, email, chid):
		#Should remove the checkout associated with the chid
		checkout = getCheckout(self, email, chid)
		if checkout:
			checkout.key.delete()
		return

#How should deletion affect checkouts and reviews?
#Look at all copies histories to find people currently holding and delete checkouts.
#Reviews should be removed.
#Is there some way to delete recursively, so we don't have duplicate code in books() and book()?
#Deletion should now work as prescribed, still needs to be tested.
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
			#Remove all reviews associated with the book.
			rquery = db_defs.Review.query(db_defs.Review.bookid == key.id())
			for rkey in rquery.iter(keys_only=True):
				rkey.delete()
			#Deactivate active checkouts of this book
			cquery = ndb.Query(ancestor=key)
			for copy in cquery.iter():
				if copy.status == 0:
					mrdate = datetime.date.min
					for entry in copy.hisEntries:
						if entry.startdate > mrdate:
							mrdate = entry.startdate
							mrentry = entry
					if mrentry:
						checkout = getCheckout(self, mrentry.email, mrentry.chid)
						if checkout:
							checkout.status = 0
							checkout.put()
				copy.key.delete()
			key.delete()

#How should deletion affect checkouts and reviews?
#Or could look at all copies histories to find people currently holding and delete checkouts.
#Reviews should also be deleted.
class book(webapp2.RequestHandler):
	def get(self, bid):
		#Should return a JSON object containing all the information for the book specified by the bid
		book = getBook(self, bid)
		if book:
			result = book.to_dict()
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
		book = getBook(self, bid)
		if book:
			if self.request.get('title'):
				if not goodInput(self, {'title': 'str'}):
					return
				book.title = self.request.get('title')
			if self.request.get('length'):
				if not goodInput(self, {'length': 'int'}):
					return
				book.length = int(self.request.get('length'))
			if self.request.get('edition'):
				if not goodInput(self, {'edition': 'int'}):
					return
				book.edition = int(self.request.get('edition'))
			if self.request.get('fname'):
				if not goodInput(self, {'fname': 'str'}):
					return
				book.author.fname = self.request.get('fname')
			if self.request.get('lname'):
				if not goodInput(self, {'lname': 'str'}):
					return
				book.author.lname = self.request.get('lname')
			if self.request.get('genres'):
				if not goodInput(self, {'genres': 'str'}):
					return
				book.genres = self.request.get('genres').split(',')
			result = book.to_dict()
			result['ID'] = book.key.id()
			self.response.write(json.dumps(result))
			book.put()
		return

	def delete(self, bid):
		#Should remove the book specified by the bid from the database
		book = getBook(self, bid)
		if book:
			#Remove all associated reviews.
			rquery = db_defs.Review.query(db_defs.Review.bookid == book.key.id())
			for rkey in rquery.iter(keys_only=True):
				rkey.delete()
			#Deactivate active checkouts of this book
			cquery = db_defs.Copy.query(ancestor=book.key)
			for copy in cquery.iter():
				if copy.status == 0:
					mrdate = datetime.date.min
					for entry in copy.hisEntries:
						if entry.startdate > mrdate:
							mrdate = entry.startdate
							mrentry = entry
					if mrentry:
						checkout = getCheckout(self, mrentry.email, mrentry.chid)
						if checkout:
							checkout.status = 0
							checkout.put()
				copy.key.delete()
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
				result = {}
				result = x.to_dict()
				result['ID'] = x.key.id()
				results.append(result)
			self.response.write(json.dumps(results))
		return

	def post(self, bid):
		#Unsupported
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

#How should deletion affect checkouts?
#Deletion should remove checkout based on most recent history entry, but not alter reviewable list.
class bookcopies(webapp2.RequestHandler):
	def get(self, bid):
		#Should return a JSON object containing the information of all the copies of the specified book
		book = getBook(self, bid)
		if book:
			copies = db_defs.Copy.query(ancestor=book.key).fetch()
			results = []
			for x in copies:
				result = {}
				result['status'] = x.status
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
			newcopy.status = 1
			result = newcopy.to_dict()
			newcopy.put()
			result['ID'] = newcopy.key.id()
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
			#Deactivate all active checkouts of all copies of this book
			cquery = ndb.Query(ancestor=book.key)
			for copy in cquery.iter():
				if copy.status == 0:
					mrdate = datetime.date.min
					for entry in copy.hisEntries:
						if entry.startdate > mrdate:
							mrdate = entry.startdate
							mrentry = entry
					if mrentry:
						checkout = getCheckout(self, mrentry.email, mrentry.chid)
						if checkout:
							checkout.status = 0
							checkout.put()
				copy.key.delete()
		return

#How should deletion affect checkouts?
#Deletion should remove checkout, but not alter reviewable list.
#Perhaps should alter status so there is no middle ground. That way changing checkout status can also alter copy status.
class copy(webapp2.RequestHandler):
	def get(self, bid, coid):
		#Should return a JSON object containing all the information associated with the specified copy
		copy = getCopy(self, bid, coid)
		if copy:
			result = copy.to_dict(exclude=['hisEntries'])
			result['hisEntries'] = []
			for x in copy.hisEntries:
				result['hisEntries'].append({'email': x.email, 'startdate': datetime.datetime.strftime(x.startdate, "%Y-%m-%d")})
			result['ID'] = copy.key.id()
			self.response.write(json.dumps(result))
		return

	def post(self, bid, coid):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsupported at this time.')
		return

	def put(self, bid, coid):
		#Should update the information for the copy specified by coid
		#Should return a JSON object containing all updated information
		copy = getCopy(self, bid, coid)
		if copy:
			if self.request.get('status'):
				if not goodInput(self, {'status': 'int'}):
					return
				copy.status = int(self.request.get('status'))
			result = copy.to_dict(exclude=['hisEntries'])
			result['hisEntries'] = []
			for x in copy.hisEntries:
				result['hisEntries'].append({'email': x.email, 'startdate': datetime.datetime.strftime(x.startdate, "%Y-%m-%d")})
			result['ID'] = copy.key.id()
			self.response.write(json.dumps(result))
			copy.put()
		return

	def delete(self, bid, coid):
		#Should remove from the database the copy specified by cid
		copy = getCopy(self, bid, coid)
		if copy:
			#Deactivate any active checkout of this copy
			if copy.status == 0:
				mrdate = datetime.date.min
				for entry in copy.hisEntries:
					if entry.startdate > mrdate:
						mrdate = entry.startdate
						mrentry = entry
				if mrentry:
					checkout = getCheckout(self, mrentry.email, mrentry.chid)
					if checkout:
						checkout.status = 0
						checkout.put()
			copy.key.delete()
		return

#Perhaps should only get, not even delete. Probably shouldn't change it at all, except through other calls (checkouts).
class copyhistory(webapp2.RequestHandler):
	def get(self, bid, coid):
		#Should return a JSON object containing a list of history entries
		copy = getCopy(self, bid, coid)
		if copy:
			history = copy.hisEntries
			results = []
			for entry in history:
				result = {}
				result['email'] = entry.email
				result['startdate'] = datetime.datetime.strftime(entry.startdate, "%Y-%m-%d")
				result['chid'] = entry.chid
				results.append(result)
			self.response.write(json.dumps(results))
		return

	def post(self, bid, coid):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsupported at this time.')
		return

	def put(self, bid, coid):
		#Unsupported
		errorMessage(self, 500, 'That feature is unsupported at this time.')
		return

	def delete(self, bid, coid):
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

#Can expand this function to check other input types and forms
#Perhaps need to check genrelist formatting?
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
		elif inputdict[key] == 'float':
			try:
				testfloat = float(handler.request.get(key))
			except:
				errorMessage(handler, 500, "Expected float for input - %s" % key)
				return False
		#Should maybe differetiate between names and general strings
		#Restrict to a subset of characters, or perhaps more reasonably exclude a subset
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
		elif inputdict[key] == 'genrelist':
			try:
				testlist = handler.request.get(key).split(',')
			except:
				errorMessage(handler, 500, "Expected comma-delineated list for input - %s" % key)
				return False

		#elif inputdict[key] == 'email':
		#Email is hard to check for validity
		#Ultimately the only sure-fire way is to send an email for verification
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

def getCopy(handler, bid, coid):
	book = getBook(handler, bid)
	if not book:
		return
	cokey = ndb.Key('Book', int(bid), 'Copy', int(coid))
	copy = cokey.get()
	if not copy:
		errorMessage(handler, 500, 'That copy is not in the system.')
	return copy 

def getCheckout(handler, email, chid):
	person = getPerson(handler, email)
	if not person:
		return
	chkey = ndb.Key('Person', email, 'Checkout', int(chid))
	checkout = chkey.get()
	if not checkout:
		errorMessage(handler, 500, 'That checkout is not in the system.')
	return checkout

def getReview(handler, rid):
	rkey = ndb.Key('Review', int(rid))
	review = rkey.get()
	if not review:
		errorMessage(handler, 500, 'That review is not in the system.')
	return review