import logging
import datetime


def pad(num):
  if num < 10:
    return "0" + num
  else:
    return "" + num


def toICALDate(d):
  return "%(year)04d%(month)02d%(day)02dT%(hour)02d%(minute)02d%(second)02d" % {
    "year": d.year,
    "month": d.month,
    "day": d.day,
    "hour": d.hour,
    "minute": d.minute,
    "second": d.second
  }


"""
* An data structure represeting a calendar and/or it's events
*
* @param {String} type The type of iCal structure i.e. VCALENDAR, VEVENT...
* @param {Object} defaultAttrs An object containing some default attributes
*  that the event will initially have.
"""
class iCal(object):
  children = []
  attributes = []
  def __init__(self, type, defaultAttrs = {}, defaultChildren = []):
    self.type = type
    self.attributes = defaultAttrs.copy()
    self.people = []
    self.children = defaultChildren[:]


  """
  * @param {String} key The name of the attribute
  * @param {Mixed} val The value of the attribute
  """
  def setAttribute(self, key, val):
    self.attributes[key] = val

  """
  * Add a child to the calendar/event...
  *
  * @param {iCal} child The child to add.
  """
  def add(self, child):
    self.children.append(child)

  """
  * Convert the iCal structure to a string which(mostly) conforms to the
  * spec <http://tools.ietf.org/html/rfc5545>.
  *
  * @returns {String}
  """
  def toString(self):
    body = ""
    attrs = self.attributes

    logging.info(attrs.keys())

    for attrName in attrs.keys():
      attr = attrs[attrName]
      logging.info(attr)
      if type(attr) == str or type(attr) == unicode:
        body += attrName + ":" + attr + "\n"
      elif type(attr) == datetime.datetime:
        body += attrName + ":" + toICALDate(attr) + "\n"
      # TODO: Add logic for things like the "ATTENDEE" attribute
      # which contains a list of "sub-attributes".

    logging.info(self.children)

    for child in self.children:
      body = body + child.toString()

    return "BEGIN:" + self.type + "\n" + body + "END:" + self.type + "\n"

class Calendar(iCal):
  def __init__(self):
    super(Calendar, self).__init__("VCALENDAR", {
      "PRODID":"-//Google Inc//Google Calendar 70.9054//EN",
      "VERSION": "2.0",
      "CALSCALE": "GREGORIAN"
    })

  def setTimezone(self, timezone):
    self.add(Timezone(timezone))
    self.setAttribute("X-WR-TIMEZONE", timezone)

class Event(iCal):
  def __init__(self):
    super(Event, self).__init__("VEVENT")


"""
@param {String} timezone The identifier for the timezone
 e.g. "Europe/Dublin"
"""
class Timezone(iCal):
  timezones = {
    "Europe/Dublin" : [
      iCal("DAYLIGHT", {
        "TZOFFSETFROM": "+0000",
        "TZOFFSETTO": "+0100",
        "TZNAME": "IST",
        "DTSTART": "19700329T010000",
        "RRULE": "FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU"
      }),
      iCal("STANDARD", {
        "TZOFFSETFROM": "+0100",
        "TZOFFSETTO": "+0000",
        "TZNAME": "GMT",
        "DTSTART": "19701025T020000",
        "RRULE": "FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU"
      })
    ]
    # TODO: Add more timezones
  }

  def __init__ (self, timezone):
    super(Timezone, self).__init__("VTIMEZONE", {
      "X-LIC-LOCATION": timezone,
      "TZID": timezone
    }, self.timezones[timezone]);
