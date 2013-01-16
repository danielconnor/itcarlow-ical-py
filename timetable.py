#var jsdom = require("jsdom");
#var ical = require("./ical");
#var util = require("util");

from BeautifulSoup import BeautifulSoup
import xml.dom.minidom as minidom
import google.appengine.api.urlfetch as urlfetch
import datetime
import logging
import ical


def textContent(node):
    text = ""

    if type(node) == minidom.Element:
        for child in node.childNodes:
            text = text + textContent(child)
    elif type(node) == minidom.Text:
        text = text + node.nodeValue

    return text


def getTimetable(url):
    """
    Get the timetable html representation and create a DOM
    structure from it to allow it to be parsed using the
    DOM javascript API

    @param {String} url The location of the timetable
    @param {Function} cb A callback function for when the
     document has been created.
    """
    url = url.replace("individual", "textspreadsheet")
    url = url.replace(" ", "%20")

    r = urlfetch.fetch(url)

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
DAYS_SHORTHAND = [
    "SU",
    "MO",
    "TU",
    "WE",
    "TH",
    "FR",
    "SA"
]


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


class Timetable():
    """
    Create a timetable data structure
    that manages multiple days. It can
    also be converted to an iCal Calendar

    @param {String} url The url that the timetable was fetched from
    """
    def __init__(self, url=""):
        self.url = url
        self.days = []

    """
    Push a Day object to the internal days array

    @param {ical.Day} day The day to add to the timetable
    """
    def addDay(self, day):
        self.days.append(day)

    """
    Creates an iCal Calendar data structure from itself.

    @returns {ical.Canendar}
    """
    def toICAL(self):
        days = self.days
        now = datetime.datetime.today()
        today = now.isoweekday()
        calendar = ical.Calendar()

        calendar.setTimezone("Europe/Dublin")

        for day in days:
            periods = day.periods
            dayVal = DAYS[day.name.lower()]
            dDate = now.replace(day=now.day + (dayVal - today))

            # set the date of the timetable day to be relative to the
            # current day so the dates are for this week
            for period in periods:
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

        logging.info(len(calendar.children))
        return calendar

# A mapping of the content of an element to it's position
# in the DOM element. Also defines an optional parse function
# if the content can be better represented in a format other
# than a string.
LAYOUT = {
    "activity": {
        "name": "name"
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
        "name": "duration"
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

    if dayElements.length < 5:
        return timetable

    # the layout will sometimes differ from staff to student
    # so the order of the columns must be generated on the fly.
    layout = []
    columns = dayElements[0].nextSibling.nextSibling.getElementsByTagName("tr")[0].getElementsByTagName("td")

    for column in columns:
        layout.append(LAYOUT[column.firstChild.data.strip().lower()])

    for dayElement in dayElements:
        day = Day(dayElement.getElementsByTagName("span")[0].firstChild.data.strip())
        rows = dayElement.nextSibling.nextSibling.getElementsByTagName("tr")

        for i in range(1, len(rows)):
            columns = rows[i].getElementsByTagName("td")
            period = {}

            for l in range(0, len(layout)):
                layoutObj = layout[l]
                col = columns[l]

                # parse the contents of the element if there's a parse
                # function available. Otherwise just assume it's text.
                if "type" in layoutObj:
                    if layoutObj["type"] == "list":
                        period[layoutObj["name"]] = parseList(getText(col).strip())
                    if layoutObj["type"] == "time":
                        period[layoutObj["name"]] = parseTime(getText(col).strip())
                else:
                    period[layoutObj["name"]] = getText(col).strip()

            day.addPeriod(period)

        # add the day to the table and set the name as
        # the name of the day
        timetable.addDay(day)

    return timetable
