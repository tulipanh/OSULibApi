from google.appengine.ext import ndb
#May need to add password storage for the Android App later, but may also do that in a completely separate implementation, or may figure out how OAuth works with GAE and Google Play Services for Android

#Status should be similar (perhaps identical) to Status for Copies (below), an integer that is interpreted by the API
class Checkout(ndb.Model):
	bookid = ndb.IntegerProperty(required=True)
	copyid = ndb.IntegerProperty(required=True)
	status = ndb.IntegerProperty(required=True)
	startdate = ndb.DateProperty(required=True)
	duedate = ndb.DateProperty(required=True)

#Two different kinds of reviews have been consolidated into one to simplify, but does lead to greater info replication
class Review(ndb.Model):
	email = ndb.StringProperty(required=True)
	fname = ndb.StringProperty(required=True)
	bookid = ndb.IntegerProperty(required=True)
	title = ndb.StringProperty(required=True)
	text = ndb.StringProperty(required=True)

class Author(ndb.Model):
	fname = ndb.StringProperty(required=True)
	lname = ndb.StringProperty(required=True)

class HisEntry(ndb.Model):
	email = ndb.StringProperty(required=True)
	duedate = ndb.DateProperty(required=True)

#Status should be an intger that is interpreted by the API
class Copy(ndb.Model):
	status = ndb.IntegerProperty(required=True)
	hisEntries = ndb.StructuredProperty(HisEntry, repeated=True)

#Should have Checkouts and Reviews as child entities
#Should use emails as key ids
#Privilege levels should be integers that are interpreted by the API
#Reviewables should be Book key ids
class Person(ndb.Model):
	fname = ndb.StringProperty(required=True)
	lname = ndb.StringProperty(required=True)
	privilege = ndb.IntegerProperty(required=True)
	reviewables = ndb.IntegerProperty(repeated=True)

#Should have Copies and Reviews as child entities
#Should use the auto-generated numbers as key ids
#Length should be the number of words in the book
#Author may not need to be a structured property, but it may not matter
class Book(ndb.Model):
	title = ndb.StringProperty(required=True)
	edition = ndb.IntegerProperty(required=True)
	length = ndb.IntegerProperty(required=True)
	genres = ndb.StringProperty(repeated=True)
	author = ndb.StructuredProperty(Author, required=True)
