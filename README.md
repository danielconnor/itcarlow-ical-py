itcarlow-ical-py
================

# About
This is currently a work in progress as it's a port from the node.js version. It's available online at
[http://itctimetable.appspot.com](http://itctimetable.appspot.com). If any issues are found you can report
them in the [issues section](https://github.com/danielconnor/itcarlow-ical-py/issues)

# API
The service exposes one endpoint: `http://itctimetable.appspot.com/timetable:format` where format is the format that you want the reponse in.

## Formats
There are currently three response formats available:

#### html
The html version provides a form that allows the user to select the modules that they want to appear in the reponse of the two other formats.

#### json
A json response with all the information that we can collect about the timetable.

```
{
  "modules": [
    {
      "name": "",
      "lecturers": [""],
      "rooms": [""]
    },
    ...
  ],
  "days": [
    {
      "name": "Monday",
      "periods": [
        {
          "name": "",         // The name of the period
          "module": "",       // The name of module associated with the module.
          "type": "",         // The type of period(normally "Lecture")
          "room": "",         // The id of the room
          "groups": [""],     // List of student groups that this period is for
          "lecturers": [""],  // List of lecturer names that teach this period
          "start": {          // Start time of the period
            "hours": 0,
            "mins": 0
          },
          "end": {            // End time of the period
            "hours": 0,
            "mins": 0
          },
          "duration": {       // Duration of the period
            "hours": 0,
            "mins": 0
          }
        }
      ]
    },
    ...
  ]
}
```

#### ics
An [http://tools.ietf.org/html/rfc5545](iCalendar) representation of the timetable. All dates represent days from the current week. Each period is set to repeat at the same time each week forever.
If the calendar is imported into Google Calendar, at the moment it will be updated at least once a day so when a new week starts, the calendar will start from
the current week and will not show for any previous weeks.

```
BEGIN:VEVENT
DESCRIPTION: %Lecturers%
SEQUENCE:1
SUMMARY: %Period name%
DTSTART;TZID=Europe/Dublin:%Start timestamp with date/day normalised to current week%
RRULE:FREQ=WEEKLY
DTEND;TZID=Europe/Dublin:%End timestamp with date/day normalised to current week%
LOCATION: %Room%
END:VEVENT
```

## Parameters
There are three parameters that the endpoint accepts:

#### item
The id of the timetable from `timetable.itcarlow.ie`.

#### type
The type of timetable being requested. This can currently either be `staff` or `student` for the corresponding timetable

#### modules
The modules parameter is a list of names of modules that should be included in any of the responses. In the case of the html
format, the selected modules will be pre-selected.

The request that is made to `timetable.itcarlow.ie` is the following with the appropriate parameters replaced.
`"http://timetable.itcarlow.ie/reporting/textspreadsheet;%(type)s;id;%(item)s?days=1-5&periods=5-40&template=%(type)s+textspreadsheet"`
