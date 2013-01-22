#!/usr/bin/env python

import webapp2
import logging
import timetable
import urllib

TIMETABLE_URL = "http://timetable.itcarlow.ie/reporting/textspreadsheet;%(type)s;id;%(item)s?days=1-5&periods=5-40&template=%(type)s+textspreadsheet"


class DefaultHandler(webapp2.RequestHandler):

        def __init__(self, request, response):
                self.initialize(request, response)

        def get(self, format):
            url = self.request.get("url")

            if not url and self.request.get("type") and self.request.get("item"):
                type = self.request.get("type")

                if type != "staff":
                    type = "student+set"

                url = TIMETABLE_URL % {
                    "type": type,
                    "item": urllib.quote(self.request.get("item"))
                    }

            try:
                t = timetable.getTimetable(url)
            except Exception, e:
                logging.info("error while trying to convert timetable: format: %s, url: %s", format, url)
                logging.error(e)
                self.response.write("error")
            else:
                logging.info("successfully converted timetable: format: %s, url: %s", format,  url)
                self.response.headers["Content-Type"] = "text/plain"
                self.response.write(t.toICAL().toString())


app = webapp2.WSGIApplication([
    ('/timetable\.(ics|json).*', DefaultHandler),
],
debug=True)
