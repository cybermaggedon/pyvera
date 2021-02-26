
# PyVera

## Introduction

Python library to allow communication with a MiCasaVerde Vera.  Operates in
both local and remote mode i.e. you can communicate directly with the Vera from
your home network, or interact with the Vera using your credentials on MCV's
relay servers if you are away from your home network.

The library provides Python API access, there are also some command-line
tools, see below.

Needs to be running UI7 for remote mode, I believe.

I'm using Linux, it may be possible use this stuff in Windows, perhaps.

## Install

```
pip3 install git+https://github.com/cybermaggedon/pyvera
```

## Examples: Writing code

### Connect to Vera

```
import vera

# Local connection using IP address on local network.
ve = vera.VeraLocal("192.168.0.10")

# Remote connection - you need your username, password and device ID.
ve = vera.VeraRemote("username", "password", "1234123456")
```

### Configure

Using a configuration file.  Create ```LUUP-AUTH.json```.  Example forms for
local access:
```
{
    "local": {
         "address": "192.168.0.10"
    }
}
````
and for remote:
```
{
  "remote": {
    "user": "USERNAME",
    "password": "PASSWORD",
    "device": "4321987654"
  }
}
```
Then just..
```
ve = vera.connect()
```

### Iterate over devices

```
for i in ve.get_devices():
    if i.room != None:
        room = i.room.name
    else:
        room = "n/a"
    print "  %s: %s (%s)" % (i.id, i.name, room)
```

### Interact with a single device

For switches:

```
# Get device by name
dev = ve.get_device("Upstairs switch")

# Report status
print "%s switch set to: %s" % (dev.name, dev.get_switch())

# Switch on
dev.set_switch(True)
```

For dimmers:

```
# Get device by name
dev = ve.get_device("Lounge dimmer")

# Report status
print "%s dimmer set to: %d" % (dev.name, dev.get_dimmer())

# Set dimmer
dev.set_dimmer(75)
```

For RGBW devices (like Aeotec ZW098):

```
# Get device by name
dev = ve.get_device("Lamp1")

# Color returned is an RGB, Daylight or Warm object.
col = dev.get_color()
print(type(col), col)

# Set color
col = vera.RGB(100, 50, 0)
#col = vera.Daylight(50)
#col = vera.Warm(150)

# Set colour
dev.set_color(col)
```

For RGBController devices:

```
# Get device by name
dev = ve.get_device("Conservatory RGB")

# Report status
print "%s set to: %d" % (dev.name, dev.get_rgb())

# Set dimmer
dev.set_rgb(vera.RGB(40, 50, 60))
#dev.set_rgb(vera.Daylight(50))
```

Thermostat example:
```
# Get the room
dev = ve.get_room("Bathroom")

# Get device specifying room
dev = ve.get_device("Bathroom stat", room=room)

# Report thermostat
print "%s current temperature: %f" % (dev.name, dev.get_temperature())
print "%s is set to: %f" % (dev.name, dev.get_setpoint())

# Set thermostat to 7 degrees.  Assuming device is set to operate in Celsius.
dev.set_setpoint(7.0)
```

A temperature/humidity sensor:
```
dev = ve.get_device("Sensor")
print "%s battery level: %d" % (dev.name, dev.get_battery())
print "%s temperature sensor: %f" % (dev.name, dev.get_temperature())
print "%s humidity sensor: %d" % (dev.name, dev.get_humidity())
```

### Discover rooms

```
rooms = ve.get_rooms()
for i in rooms:
    print "  %s: %s" % (i.id, i.name)
```

### Discover scenes

```
scenes = ve.get_scenes()
for i in scenes:
    print "  %s: %s" % (i.id, i.name)
```

### Run scene

```
# Get room
room = ve.get_room("Heating")

# Iterate, find scene and execute it.
scenes = ve.get_scenes()
for i in scenes:
    if i.name == "Hot water":
        i.run()
```

### Delete scenes

```
# Get room
room = ve.get_room("Heating")

# Iterate, find scenes in a room and delete them
scenes = ve.get_scenes()
for i in scenes:
    if i.room == room:
        i.delete()
```

### Create a scene

```
# This is a complicated example, it doesn't have to be this complicated :)
# Timer, on Mon, Weds, Thurs, 10:30.
t1 = vera.DayOfWeekTimer(4, "on", "1,3,4", vera.Time(10, 30))

# Every 12 minutes
t2 = vera.IntervalTimer(5, "switch on", minutes=12)

# 12:30 on 3/6/2016.
t3 = vera.AbsoluteTimer(6, "absolute time", 2016, 6, 3, 12, 30)

# 10:30 on 1st, 3rd, 4th and 21st of the month.
t4 = vera.DayOfMonthTimer(1, "some days", "1,3,4,21", vera.Time(10, 30))

# Scene only works in Home and Night modes.
m = vera.Modes(home=True, night=True)

# Get a device for a trigger
dev1 = ve.get_device("Sensor")

# Room for the scene.
r = ve.get_room("Heating")

# Create a trigger.  Template 1 for this device was a battery test.  Arguments
# has number 12, so this would trigger when battery goes below 12%.
# stop, start and days_of_week can optionally limit the time period when the
# trigger is valid i.e. this is 10:30-11:30 on Mon, Fri, Sat.
tr = vera.Trigger(id=41, name="trigger", device=dev1, template=1, args=[12],
                  start=vera.Time(10,30), stop=vera.Time(11, 30),
                  days_of_week="1,5,6")

# Get a thermostat
dev2 = ve.get_device("Attic stat")

# Get a switch
dev3 = ve.get_device("Switch 4")

# Define a 'set point' action, which modifies thermostat setting.
spa = vera.SetpointAction(dev2, 8.0)

# Define a 'switch' action, operates a simple switch.
sa = vera.SwitchAction(dev3, 1)

# Create an action set of the two actions, which operates after a 10-second
# delay.
acts = vera.Group(10, [spa, sa])

# Create scene definition, containing name, triggers, modes, timers, actions
# and the room.
sd = vera.SceneDefinition("My complicated scene", [tr], m, [t1, t2, t3, t4],
                          [acts], r)

# Create the scene.
ve.create_scene(sd)
```

## Command-line utilites

It can be fiddly to manage a heating schedule for a large heating system
through the web interface, so I've got some utilities that allow the schedule
to be stored in a file, and pushed to the Vera.

### Create a CSV file contain the schedule

See ```SCHEDULE.csv``` for a example format.

Format is:
1. Scene name
2. Device to manage.
3. Type of action to take:
--* ```heat``` to manage a heating controller.
--* ```set``` to manage a thermostat.
--* ```switch``` to operate a simple switch.
4. Value to apply to the device:
--* For ```heat``` use values ```HeatOn``` and ```Off```.
--* For ```set``` using a floating point temperature value.
--* For ```switch``` Use ```On``` and ```Off```.
5. The rest of the fields are pairs of days in week, and times.
   The days of week are a comma-separated list of digits representing
   days 1=Monday etc.  Times are colon-separated 24-hour times.

e.g.

```
Ground floor on,Ground floor stat,set,11.0,"1,2,3,4,5",06:30,"1,2,3,4,5",17:30,"6,7",09:30
```

### Configure

Create a file e.g. ```AUTH.json```.  Example forms for local comms to Vera:
```
{
    "local": {
         "address": "192.168.0.10"
    }
}
````
and for remote:
```
{
  "remote": {
    "user": "USERNAME",
    "password": "PASSWORD",
    "device": "4321987654"
  }
}
```

Also, using the web interface, make sure there's a room for the scenes to be
created in.  When uploading, all scenes in the room get deleted, so you
probably want a separate room e.g. Heating.

### Create scenes

Parameters to this utility are the configuration file, and the room name.  The
schedule is read from the standard input.

```
vera-upload-scenes AUTH.json Heating < SCHEDULE.csv
```

If all works, you should see a set of scenes appear in the web interface.

The `vera-upload-scenes` utility uses a restricted set of the
scene features, so may get confused if you start creating your own
scenes in the room.

The `vera-get-scenes` utility returns the scenes as a CSV file...

```
vera-get-scenes AUTH.json Heating
```

and the `vear-delete-scenes` utility deletes all scenes in a room...

```
vera-delete-scenes AUTH.json Heating
```

### Weather

The weather API is reverse-engineered, don't rely on this.

```
vera-get-weather AUTH.json
```

