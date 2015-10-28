import webapp2

app = webapp2.WSGIApplication([
    ('/', 'api.mainpage'),
    webapp2.Route(r'/people', 'api.people'),
    webapp2.Route(r'/people/<email>', 'api.person'),
    webapp2.Route(r'/people/<email>/reviews', 'api.personreviews'),
    webapp2.Route(r'/reviews/<rid:[0-9]+>', 'api.review'),
    webapp2.Route(r'/people/<email>/checkouts', 'api.personcheckouts'),
    webapp2.Route(r'/checkouts/<chid:[0-9]+>', 'api.checkout'),
    webapp2.Route(r'/books', 'api.books'),
    webapp2.Route(r'/books/<bid:[0-9]+>', 'api.book'),
    webapp2.Route(r'/books/<bid:[0-9]+>/reviews', 'api.bookreviews'),
    webapp2.Route(r'/books/<bid:[0-9]+>/copies', 'api.bookcopies'),
    webapp2.Route(r'/copies/<coid:[0-9]+>', 'api.copy'),
    webapp2.Route(r'/copies/<coid:[0-9]+>/history', 'api.copyhistory'),
    ], debug=True)