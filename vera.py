
import urllib, urllib2, json
import sys
import sha
import base64
import httplib
import time
import requests

class Time(object):

    def __init__(self, h=0, m=0, s=0, after_sunrise=False, after_sunset=False):
        self.time = (h, m, s)
        self.after_sunrise = after_sunrise
        self.after_sunset = after_sunset

    def output(self):
        if self.after_sunrise:
            return "%02d:%02d:%02dR" % self.time
        if self.after_sunset:
            return "%02d:%02d:%02dT" % self.time
        return "%02d:%02d:%02d" % self.time

    def parse(s):
        x = s.split(":")
        if len(x) == 1:
            x.append("0")
        if len(x) == 2:
            x.append("0")
        
        return Time(int(x[0]), int(x[1]), int(x[2]))

    parse = staticmethod(parse)

class Timer(object):

    def parse(s):

        if s["type"] == 2:
            return DayOfWeekTimer.parse(s)

        if s["type"] == 3:
            return DayOfMonthTimer.parse(s)

        raise RuntimeError, "Parsing timer not implemented."

    parse = staticmethod(parse)

class DayOfWeekTimer(Timer):

    def __init__(self, id=None, name=None, days=None, time=None):
        self.id = id
        self.name = name
        self.days = days
        self.time = time

    def output(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": 2,
            "enabled": 1,
            "days_of_week": self.days,
            "time": self.time.output()
       }

    def parse(s):
        t = DayOfWeekTimer()
        t.id = s.get("id", None)
        t.name = s.get("name", None)
        t.days = s.get("days_of_week", None)
        if s.has_key("time"):
            t.time = Time.parse(s["time"])
        else:
            t.time = None
        return t

    parse = staticmethod(parse)
    
class DayOfMonthTimer(Timer):

    def __init__(self, id, name, days, time):
        self.id = id
        self.name = name
        self.days = days
        self.time = time

    def output(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": 3,
            "enabled": 1,
            "days_of_month": self.days,
            "time": self.time.output()
        }

    def parse(s):
        t = DayOfMonthTimer()
        t.id = s.get("id", None)
        t.name = s.get("name", None)
        t.days = s.get("days_of_month", None)
        if s.has_key("time"):
            t.time = Time.parse(s["time"])
        else:
            t.time = None
        return t

    parse = staticmethod(parse)

    
class IntervalTimer(Timer):
    def __init__(self, id, name, seconds=0, minutes=0, hours=0, days=0):
        self.id = id
        self.name = name
        (self.seconds, self.minutes, self.hours, self.days) = \
            (seconds, minutes, hours, days)

    def output(self):
        
        if self.days > 0:
            interval = "%dd" % self.days
        if self.hours > 0:
            interval = "%dh" % self.hours
        if self.minutes > 0:
            interval = "%dm" % self.minutes
        else:
            interval = "%ds" % self.seconds
        
        return {
            "id": self.id,
            "name": self.name,
            "type": 1,
            "enabled": 1,
            "interval": interval
        }

class AbsoluteTimer(object):

    def __init__(self, id, name, year, month, date, hours=0, minutes=0,
                 seconds=0):
        self.id, self.name = id, name
        (self.year, self.month, self.date) = (year, month, date)
        (self.hours, self.minutes, self.seconds) = (hours, minutes, seconds)

    def output(self):
        time = "%04d-%02d-%02d %02d:%02d:%02d" % (self.year, self.month, \
                self.date, self.hours, self.minutes, self.seconds)
        return {
            "id": self.id,
            "name": self.name,
            "type": 4,
            "enabled": 1,
            "abstime": time
        }

class Trigger(Timer):
    
    def __init__(self, id=None, name=None, device=None, template=None, args=[],
                 start=None, stop=None, days_of_week=None):
        self.id, self.name = id, name
        self.device = device
        self.template = template
        self.args = args
        self.start, self.stop = start, stop
        self.days_of_week = days_of_week

    def output(self):
        args = []
        for i in range(0, len(self.args)):
            args.append({"id": i + 1, "value": self.args[i]})

        val = {
            "device": self.device.id,
            "enabled": 1,
            "name": self.name,
            "template": self.template,
            "arguments": args
        }

        if self.start != None and self.stop != None:
            val["start"] = self.start.output()
            val["stop"] = self.stop.output()

        if self.days_of_week != None:
            val["days_of_week"] = self.days_of_week

        return val

    def parse(vera, s):

        t = Trigger()

        t.id = s.get("id", None)
        t.template = s.get("template", None)
        t.name = s.get("name", None)
        t.days_of_week = s.get("days_of_week", None)
        
        if s.has_key("arguments"):
            for i in s["arguments"]:
                t.args.append(i["value"])

        if s.has_key("device"):
            t.device = vera.get_device_by_id(s["device"])
        else:
            t.device = None

        if s.has_key("start"):
            t.start = Time.parse(s["start"])
        else:
            t.start = None

        if s.has_key("stop"):
            t.stop = Time.parse(s["stop"])
        else:
            t.stop = None

        return t

    parse = staticmethod(parse)

class Action(object):

    def parse(vera, s):

        if s["service"] == "urn:upnp-org:serviceId:TemperatureSetpoint1":
            return SetpointAction.parse(vera, s)

        if s["service"] == "urn:upnp-org:serviceId:SwitchPower1":
            return SwitchAction.parse(vera, s)

        if s["service"] == "urn:upnp-org:serviceId:HVAC_UserOperatingMode1":
            return HeatingAction.parse(vera, s)

        raise RuntimeError, "Don't know how to handle service %s" % \
            s["service"]

    parse = staticmethod(parse)

class SetpointAction(Action):

    def __init__(self, device=None, value=None):
        self.device = device
        self.value = value

    def output(self):
        return {
            "device": self.device.id, 
            "action": "SetCurrentSetpoint", 
            "arguments": [
                {
                    "name": "NewCurrentSetpoint", 
                    "value": self.value
                }
            ], 
            "service": "urn:upnp-org:serviceId:TemperatureSetpoint1"
        }
    
    def parse(vera, s):
        ha = SetpointAction()
        ha.device = vera.get_device_by_id(s["device"])
        ha.value = s["arguments"][0]["value"]
        return ha

    parse = staticmethod(parse)

class SwitchAction(Action):

    def __init__(self, device=None, value=None):
        self.device = device
        self.value = value

    def output(self):
        return {
            "device": self.device.id, 
            "action": "SetTarget", 
            "arguments": [
                {
                    "name": "newTargetValue", 
                    "value": self.value
                }
            ], 
            "service": "urn:upnp-org:serviceId:SwitchPower1"
        }

    def parse(vera, s):
        ha = SwitchAction()
        ha.device = vera.get_device_by_id(s["device"])
        ha.value = s["arguments"][0]["value"]
        return ha

    parse = staticmethod(parse)

class HeatingAction(Action):

    def __init__(self, device=None, value=None):
        self.device = device
        self.value = value

    def output(self):
        return {
            "device": self.device.id, 
            "action": "SetModeTarget", 
            "arguments": [
                {
                    "name": "NewModeTarget", 
                    "value": self.value
                }
            ], 
            "service": "urn:upnp-org:serviceId:HVAC_UserOperatingMode1"
        }

    def parse(vera, s):
        ha = HeatingAction()
        ha.device = vera.get_device_by_id(s["device"])
        ha.value = s["arguments"][0]["value"]
        return ha

    parse = staticmethod(parse)

class ActionSet(object):

    def __init__(self, delay=None, actions=None):
        self.delay = delay
        self.actions = actions

        if self.actions == None: self.actions = []

    def output(self):
        acts = []
        for i in self.actions:
            acts.append(i.output())
        return {
            "delay": self.delay,
            "actions": acts
        }

    def parse(vera, s):
        aset = ActionSet()

        aset.delay = s.get("delay", 0)

        if s.has_key("actions"):
            for i in s["actions"]:
                aset.actions.append(Action.parse(vera, i))

        return aset

    parse = staticmethod(parse)

class SceneDefinition(object):

    def __init__(self, name=None, triggers=None, modes=None, timers=None,
                 actions=None, room=None):

        self.name = name

        if triggers != None:
            self.triggers = triggers
        else:
            self.triggers = []
            
        self.modes = modes

        if timers != None:
            self.timers = timers
        else:
            self.timers = []

        if actions != None:
            self.actions = actions
        else:
            self.actions = []

        self.room = room

    def output(self):

        triggers = []
        for i in self.triggers:
            triggers.append(i.output())

        timers = []
        for i in self.timers:
            timers.append(i.output())

        actions = []
        for i in self.actions:
            actions.append(i.output())

        val = {
            "name": self.name,
            "triggers": triggers,
            "triggers_operator": "OR", 
            "timers": timers,
            "groups": actions,
            "users": "", 
        }

        if self.modes != None:
            val["modeStatus"] = self.modes.output()

        if self.room != None:
            val["room"] = self.room.id

        return val

    def parse(vera, s):

        sd = SceneDefinition()
        
        sd.name = s["name"]

        for i in s["triggers"]:
            sd.triggers.append(Trigger.parse(vera, i))

        if s.has_key("timers"):
            for i in s["timers"]:
                sd.timers.append(Timer.parse(i))

        if s.has_key("groups"):
            for i in s["groups"]:
                sd.actions.append(ActionSet.parse(vera, i))

        if s.has_key("room"):
            if s["room"] == 0:
                sd.room = None
            else:
                sd.room = vera.get_room_by_id(s["room"])

        if s.has_key("modeStatus"):
            sd.modes = Modes.parse(vera, s["modeStatus"])

        return sd

    parse = staticmethod(parse)

class Modes(object):
    def __init__(self, home=False, away=False, night=False, vacation=False):
        self.home, self.away, self.night = home, away, night
        self.vacation = vacation

    def output(self):
        val = ""
        if self.home:
            val = "1"
        if self.away:
            if val != "": val = val + ","
            val = val + "2"
        if self.night:
            if val != "": val = val + ","
            val = val + "3"
        if self.vacation:
            if val != "": val = val + ","
            val = val + "4"
        return val

    def parse(vera, s):
        x = s.split(",")
        y = {}
        for i in x:
            y[i] = True

        m = Modes()
        m.home = y.get(0, None)
        m.away = y.get(1, None)
        m.night = y.get(2, None)
        m.vacation = y.get(3, None)

    parse = staticmethod(parse)

class Device(object):

    def __init__(self):
        pass

    def get_switch(self):
        action = "variableget"
        svc = "urn:upnp-org:serviceId:SwitchPower1"
        var = "Status"
        path = "data_request?id=%s&DeviceNum=%d&serviceId=%s&Variable=%s" \
               % (action, self.id, svc, var)
        status = self.vera.get(path)

        return status == 1

    def set_switch(self, value):
        if value:
            value = 1
        else:
            value = 0
            
        action = "variableset"
        svc = "urn:upnp-org:serviceId:SwitchPower1"
        var = "Status"
        path = "data_request?id=%s&DeviceNum=%d&serviceId=%s&Variable=%s&Value=%d" \
               % (action, self.id, svc, var, value)
        status = self.vera.get(path)
        return status

    def get_current_temperature(self):
        action = "variableget"
        svc = "urn:upnp-org:serviceId:TemperatureSensor1"
        var = "CurrentTemperature"
        path = "data_request?id=%s&DeviceNum=%d&serviceId=%s&Variable=%s" \
               % (action, self.id, svc, var)
        status = self.vera.get(path)
        return status

    def get_current_humidity(self):
        action = "variableget"
        svc = "urn:micasaverde-com:serviceId:HumiditySensor1"
        var = "CurrentLevel"
        path = "data_request?id=%s&DeviceNum=%d&serviceId=%s&Variable=%s" \
               % (action, self.id, svc, var)
        status = self.vera.get(path)
        return status

    def get_set_point(self):
        action = "variableget"
        svc = "urn:upnp-org:serviceId:TemperatureSetpoint1"
        var = "CurrentSetpoint"
        path = "data_request?id=%s&DeviceNum=%d&serviceId=%s&Variable=%s" \
               % (action, self.id, svc, var)
        status = self.vera.get(path)
        return status

    def set_set_point(self, value):
        action = "variableset"
        svc = "urn:upnp-org:serviceId:TemperatureSetpoint1"
        var = "CurrentSetpoint"
        path = "data_request?id=%s&DeviceNum=%d&serviceId=%s&Variable=%s&Value=%f" \
               % (action, self.id, svc, var, value)
        status = self.vera.get(path)
        return status

    def get_battery(self):
        action = "variableget"
        svc = "urn:micasaverde-com:serviceId:HaDevice1"
        var = "BatteryLevel"
        path = "data_request?id=%s&DeviceNum=%d&serviceId=%s&Variable=%s" \
               % (action, self.id, svc, var)
        status = self.vera.get(path)
        return status

class Scene(object):

    def __init__(self):
        pass

class Room(object):

    def __init__(self):
        pass

class Vera(object):

    def __init__(self):
        self.update_state()

    def update_state(self):
        ud = self.get('data_request?id=user_data&output_format=json')
        self.user_data = ud

        self.rooms = {}
        for i in self.user_data["rooms"]:
            s = Room()
            s.vera = self
            s.id = i["id"]
            s.name = i["name"]
            self.rooms[s.id] = s

        self.devices = {}
        for i in self.user_data["devices"]:

            d = Device()
            d.vera = self
            d.id = i["id"]
            d.name = i["name"]

            if i.has_key("manufacturer"):
                d.manufacturer = i["manufacturer"]
            else:
                d.manufacturer = None

            if i.has_key("model"):
                d.model = i["model"]
            else:
                d.model = None

            d.device_type = i["device_type"]

            if i.has_key("device_file"):
                d.device_file = i["device_file"]
                
            if i.has_key("device_json"):
                d.device_json = i["device_json"]

            if i.has_key("invisible") and int(i["invisible"]) > 0:
                d.invisible = True
            else:
                d.invisible = False
            
            if i.has_key("room") and self.rooms.has_key(int(i["room"])):
                d.room = self.rooms[int(i["room"])]
            else:
                d.room = None
            self.devices[d.id] = d

        self.scenes = {}

        for i in self.user_data["scenes"]:

            s = Scene()
            
            s.vera = self
            s.id = i["id"]
            s.name = i["name"]
            if self.rooms.has_key(int(i["room"])):
                s.room = self.rooms[int(i["room"])]
            else:
                s.room = None

            s.definition = SceneDefinition.parse(self, i)
            
            self.scenes[s.id] = s

    def get_room_by_id(self, id):
        if self.rooms.has_key(id):
            return self.rooms[id]
        raise RuntimeError, "Room not known"

    def get_room(self, name):
        for i in self.rooms:
            if self.rooms[i].name == name:
                return self.rooms[i]
        raise RuntimeError, "Room '%s' not known" % name

    def get_device(self, name, room=None):
        for i in self.devices:
            if self.devices[i].name == name:
                if room == None or self.devices[i].room == room:
                    return self.devices[i]
        raise RuntimeError, "Device '%s' not known" % name

    def get_device_by_id(self, id):
        for i in self.devices:
            if self.devices[i].id == id:
                return self.devices[i]
        raise RuntimeError, "Device not found"

    def get_devices(self):

        devices = []
        for i in self.devices:
            devices.append(self.devices[i])

        return devices

    def get_scenes(self):

        scenes = []
        for i in self.scenes:
            scenes.append(self.scenes[i])

        return scenes

    def get_rooms(self):

        rooms = []
        for i in self.rooms:
            rooms.append(self.rooms[i])

        return rooms

    def get(self, path):
        raise RuntimeError("Not implemented")

    def get_user_data(self):
        return self.user_data
  
    def get_sdata(self):

        payload = self.get('data_request?id=sdata&output_format=json')
        return payload

    def get_file(self, path):
        file = self.get('data_request?id=file&parameters=%s' % path)
        return file
  
    def get_status(self):

        payload = self.get('data_request?id=status&output_format=json')
        return payload
  
    def get_scene(self, id):

        payload = self.get('data_request?id=scene&action=list&scene=%s&output_format=json' % id)
        return payload
    
    def delete_scene(self, s):

        return self.get('data_request?id=scene&action=delete&scene=%s' % s.id)
  
    def create_scene(self, s):

        s = json.dumps(s.output())

        # URL-encoding.  Vera not happy with Python's standard
        # URL-encoding.
        s = s.replace("%", "%25")
        s = s.replace(":", "%3a")
        s = s.replace("+", "%2b")
        s = s.replace("&", "%26")
        s = s.replace("{", "%7b")
        s = s.replace("}", "%7d")
        s = s.replace("'", "%27")
        s = s.replace('"', "%22")
        s = s.replace("?", "%3f")
        s = s.replace(" ", "%20")
        
        payload = self.get('data_request?id=scene&action=create&json=%s' % s)
        return payload

class VeraLocal(Vera):

    def __init__(self, host, port = 3480):
        self.host = host
        self.port = port
        Vera.__init__(self)

    def get(self, path):
        base = 'http://%s:%d' % (self.host, self.port)
        url = '%s/%s' % (base, path)

        conn = urllib2.urlopen(url)
        payload = conn.read()
        try: 
            payload = json.loads(payload)
        except:
            payload = None

        conn.close()

        return payload

class VeraRemote(Vera):

    def get_session_token(self, server):

        headers = {"MMSAuth": self.auth_token, "MMSAuthSig": self.auth_sig}
        url = "https://%s/info/session/token" % server
        session_token = self.session.get(url, headers=headers).text

        return session_token

    def __init__(self, user, password, device):
        self.user = user
        self.password = password
        self.device = device
        self.session = requests.session()

        # Hard-coded auth seed
        seed = "oZ7QE6LcLJp6fiWzdqZc"

        # Get auth tokens
        sha1p = sha.new(user.lower() + password + seed)
        sha1p = sha1p.hexdigest()

        auth_server = "vera-us-oem-autha11.mios.com"

        url = "https://%s/autha/auth/username/%s?SHA1Password=%s&PK_Oem=1" % \
              (auth_server, user.lower(), sha1p)

        response = self.session.get(url).json()

        self.server_account = response["Server_Account"]
        self.auth_token = response["Identity"]
        self.auth_sig = response["IdentitySignature"]

        # Get account number
        account_info = json.loads(base64.b64decode(self.auth_token))
        pk_account = account_info["PK_Account"]
        sys.stderr.write("Account number: %s\n" % pk_account)

        # Get session token for server account
        session_token = self.get_session_token(self.server_account)

        # Get devices
        headers = { "MMSSession": session_token }
        url = "https://%s/account/account/account/%s/devices" % \
              (self.server_account, str(pk_account))
        devices = self.session.get(url, headers=headers).json()

        # Work out server device
        server_device = None
        for i in devices["Devices"]:
            if i["PK_Device"] == device:
                server_device = i["Server_Device"]
        if server_device == None:
            raise RuntimeError, "Device %s not known.\n" % device
                
        sys.stderr.write("Server device: %s\n" % server_device)

        # Get session token on server_device
        session_token = self.get_session_token(server_device)

        # Get server_relay
        headers = { "MMSSession": session_token }

        url = "https://" + server_device + "/device/device/device/" + str(device)

        relay_info = self.session.get(url, headers=headers).json()

        self.relay = relay_info["Server_Relay"]

        sys.stderr.write("Server relay: %s\n" % self.relay)

        # Get session token on server_relay
        self.session_token = self.get_session_token(self.relay)

        Vera.__init__(self)

        sys.stderr.write("Connected to remote device.\n")

    def get(self, path):

        headers = { "MMSSession": self.session_token }

        url = "https://%s/relay/relay/relay/device/%s/port_3480/%s" % (self.relay, str(self.device), path)

        response = requests.get(url, headers=headers)

        try: 
            return response.json()
        except:
            pass

        return response.text
        
