#!/usr/bin/env python

import webapp2
import logging
import timetable


class DefaultHandler(webapp2.RequestHandler):

        def __init__(self, request, response):
                self.initialize(request, response)

        def get(self, format):
            logging.info(format)

            url = self.request.get("url")

            if not url and self.request.get("type") and self.request.get("item"):
                type = self.request.get("type")

                if type != "staff":
                    type = "student+set"

                url = "http://timetable.itcarlow.ie/reporting/textspreadsheet;" + type + ";id;" + self.request.get("item") + "?days=1-5&periods=5-40&template=" + type + "+textspreadsheet"

            try:
                t = timetable.getTimetable(url)
            except:
                self.response.write("error")
            else:
                self.response.headers["Content-Type"] = "text/plain"
                self.response.write(t.toICAL().toString())


app = webapp2.WSGIApplication([
    ('/timetable\.(ics|json).*', DefaultHandler),
],
debug=True)
