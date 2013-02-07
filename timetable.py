#var jsdom = require("jsdom");
#var ical = require("./ical");
#var util = require("util");

from BeautifulSoup import BeautifulSoup
import xml.dom.minidom as minidom
import google.appengine.api.urlfetch as urlfetch
import datetime
import ical
import logging
import re


def getTimetable(url):
    """
    Get the timetable html representation and create a DOM
    structure from it to allow it to be parsed using the
    DOM javascript API

    @param {str} url The location of the timetable
    """

    # textspreadsheet is easier to parse
    url = url.replace("individual", "textspreadsheet")

    r = urlfetch.fetch(url)

    # We parse the page twice, once using BeautifulSoup, then again
    # using minidom. We do this because the minidom api better reflects
    # that of the actual DOM API and it made it easier to convert from the
    # node.js version.
    # TODO: Consider revising
    return parseTimetable(minidom.parseString(BeautifulSoup(r.content).prettify()), url)

"""
Quick reference to the days and their values
according to the Date object.
"""
DAYS = {
    "monday":    1,
    "tuesday":   2,
    "wednesday": 3,
    "thursday":  4,
    "friday":    5,
    "saturday":  6,
    "sunday":    7
}


def parseTime(str):
    """
    Convert a string in the form "hh:mm" to an object
    representation
    """
    parts = str.split(":")
    return {
        "hours": int(parts[0]),
        "mins": int(parts[1])
    }


def parseList(str):
    """
    Split a list delimted by a ";"
    """
    return str.split(";")


class Day():
    """
    @param {String} name The name of the day i.e. Monday, Tuesday...
    """
    def __init__(self, name):
        self.name = name
        self.periods = []

    def addPeriod(self, period):
        self.periods.append(period)


class Module():

    def __init__(self, period):
        self.name = ""
        self.rooms = []
        self.times = []
        self.lecturers = []
        self.update(period)

    def update(self, period):
        if "lecturers" in period:
            for lecturer in period["lecturers"]:
                if not lecturer in self.lecturers:
                    self.lecturers.append(lecturer)

        if "room" in period:
            if not period["room"] in self.rooms:
                self.rooms.append(period["room"])

        self.name = period["name"]


class Timetable():

    def __init__(self, url=""):
        """
        Create a timetable data structure
        that manages multiple days. It can
        also be converted to an iCal Calendar

        @param {String} url The url that the timetable was fetched from
        """
        self.url = url
        self.days = []
        self.modules = {}

    def addDay(self, day):
        """
        Push a Day object to the internal days array

        @param {ical.Day} day The day to add to the timetable
        """
        self.days.append(day)

    def updateModule(self, period):
        """
        Update the information we have about each module based on
        each period that we encounter.
        """
        name = period["name"]

        if not name in self.modules:
            self.modules[name] = Module(period)
        else:
            self.modules[name].update(period)

    def toICAL(self, modules=[]):
        """
        Creates an iCal Calendar data structure from itself.

        @returns {ical.Canendar}
        """
        days = self.days
        now = datetime.datetime.today()
        today = now.isoweekday()
        calendar = ical.Calendar()

        calendar.setTimezone("Europe/Dublin")

        for day in days:
            periods = day.periods
            dayVal = DAYS[day.name.lower()]
            dDate = now + ((dayVal - today) * datetime.timedelta(days=1))

            # set the date of the timetable day to be relative to the
            # current day so the dates are for this week
            for period in periods:
                if len(modules) == 0 or period["name"] in modules:
                    event = ical.Event()

                    event.setAttribute("DTSTART;TZID=Europe/Dublin", dDate.replace(
                        hour=period["start"]["hours"],
                        minute=period["start"]["mins"],
                        second=0))
                    event.setAttribute("DTEND;TZID=Europe/Dublin", dDate.replace(
                        hour=period["end"]["hours"],
                        minute=period["end"]["mins"],
                        second=0))
                    event.setAttribute("SUMMARY", period["name"])
                    event.setAttribute("DESCRIPTION", ";".join(period["lecturers"]))
                    event.setAttribute("LOCATION", period["room"])
                    event.setAttribute("RRULE", "FREQ=WEEKLY")
                    event.setAttribute("SEQUENCE", "1")

                    calendar.add(event)

        return calendar

# A mapping of the content of an element to it's position
# in the DOM element.
LAYOUT = {
    "activity": {
        "name": "name",
        "regex": "(.+)\s*\/.*"
    },
    "module": {
        "name": "module"
    },
    "type": {
        "name": "type"
    },
    "start": {
        "name": "start",
        "type": "time"
    },
    "end": {
        "name": "end",
        "type": "time"
    },
    "duration": {
        "name": "duration",
        "type": "time"
    },
    "weeks": {
        "name": "weeks"
    },
    "room": {
        "name": "room"
    },
    "staff": {
        "name": "lecturers",
        "type": "list"
    },
    "student groups": {
        "name": "groups",
        "type": "list"
    }
}


def getText(node):
    """
    Get the text content of the node and all subnodes.

    Similar to Element.textContent of DOM API.
    """
    rc = []

    for n in node.childNodes:
        if n.nodeType == n.TEXT_NODE:
            rc.append(n.data)
        else:
            rc.append(getText(n))

    return ''.join(rc)


def parseTimetable(document, url):
    """
    Takes a document and parses the timetable information from it.

    @param {Document} document A DOM document that contains a timetable
     in the format found at timetable.itcarlow.ie. The timtable should
     be in "list" format, as it's easier to parse and contains more
     information on the timetable.
    """
    document.normalize()
    dayElements = document.getElementsByTagName("p")
    timetable = Timetable(url)

    if not dayElements.length:
        # logging.info(document.toprettyxml())
        logging.info("not enough days")
        return timetable

    # the layout will sometimes differ from staff to student
    # so the order of the columns must be generated on the fly.
    layout = []

    table = dayElements[0]

    while table and table.nodeName != "table":
        table = table.nextSibling

    if not table or table.nodeName != "table":
        logging.info("not a table")
        return timetable

    rows = table.getElementsByTagName("tr")

    if not rows or not rows.length:
        logging.info("no rows")
        return timetable

    columns = rows[0].getElementsByTagName("td")

    for column in columns:
        layout.append(LAYOUT[column.firstChild.data.strip().lower()])

    for dayElement in dayElements:
        day = Day(dayElement.getElementsByTagName("span")[0].firstChild.data.strip())

        rows = dayElement.nextSibling.nextSibling.getElementsByTagName("tr")

        for i in range(1, rows.length):
            columns = rows[i].getElementsByTagName("td")
            period = {}

            for l in range(0, len(layout)):
                layoutObj = layout[l]
                text = getText(columns[l]).strip()

                if "regex" in layoutObj:
                    match = re.search(layoutObj["regex"], text)
                    if match:
                        text = match.group(1)

                # We only need to parse list or time strings
                # otherwise just store the text.
                if "type" in layoutObj:
                    if layoutObj["type"] == "list":
                        period[layoutObj["name"]] = parseList(text)
                    if layoutObj["type"] == "time":
                        period[layoutObj["name"]] = parseTime(text)
                else:
                    period[layoutObj["name"]] = text

            timetable.updateModule(period)

            day.addPeriod(period)

        # add the day to the table and set the name as
        # the name of the day
        timetable.addDay(day)

    return timetable
