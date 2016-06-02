
# PyVera

## Introducation

Python library to allow communication with a MiCasaVerde Vera.  Operates in
both local and remote mode i.e. you can communicate directly with the Vera from
your home network, or interact with the Vera using your credentials on MCV's
relay servers if you are away from your home network.

Needs to be running UI7 for remote mode, I believe.

## Examples

### Connect to Vera

```
import vera

# Local connection using IP address on local network.
ve = vera.VeraLocal("192.168.0.10")

# Remote connection - you need your username, password and device ID.
ve = vera.VeraRemote("username", "password", "1234123456")
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

Thermostat example:
```
# Get the room
dev = ve.get_room("Bathroom")

# Get device specifying room
dev = ve.get_device("Bathroom stat", room=room)

# Report thermostat
print "%s current temperature: %f" % (dev.name, dev.get_current_temperature())
print "%s is set to: %f" % (dev.name, dev.get_set_point())

# Set thermostat to 7 degrees.  Assuming device is set to operate in Celsius.
dev.set_set_point(7.0)
```

A temperature/humidity sensor:
```
dev = ve.get_device("Sensor")
print "%s battery level: %d" % (dev.name, dev.get_battery())
print "%s temperature sensor: %f" % (dev.name, dev.get_current_temperature())
print "%s humidity sensor: %d" % (dev.name, dev.get_current_humidity())
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

### Delete scenes

```
# Get room
room = ve.get_room("Heating")

# Iterate, deleting all Heating scenes.
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
acts = vera.ActionSet(10, [spa, sa])

# Create scene definition, containing name, triggers, modes, timers, actions
# and the room.
sd = vera.SceneDefinition("My complicated scene", [tr], m, [t1, t2, t3, t4],
                          [acts], r)

# Create the scene.
ve.create_scene(sd)
```

