
import unittest
import vera
import json

class TestTime(unittest.TestCase):

    def test_construction(self):
        t = vera.Time(13, 0, 0)
        self.assertEqual(t.output(), "13:00:00")
        t = vera.Time(13, 28, 0)
        self.assertEqual(t.output(), "13:28:00")
        t = vera.Time(13, 28, 54)
        self.assertEqual(t.output(), "13:28:54")
        t = vera.Time(13)
        self.assertEqual(t.output(), "13:00:00")
        t = vera.Time(13, 28)
        self.assertEqual(t.output(), "13:28:00")
        t = vera.Time(13, 28, 54)
        self.assertEqual(t.output(), "13:28:54")
        t = vera.Time(9, 14, 21, after_sunrise=True)
        self.assertEqual(t.output(), "09:14:21R")
        t = vera.Time(21, 1, 59, after_sunset=True)
        self.assertEqual(t.output(), "21:01:59T")

    def test_parse(self):
        t = vera.Time.parse("13:14:15")
        self.assertEqual(vera.Time(13, 14, 15), t)
        t = vera.Time.parse("13:14")
        self.assertEqual(vera.Time(13, 14), t)
        t = vera.Time.parse("13")
        self.assertEqual(vera.Time(13), t)
        t = vera.Time.parse("13:14:15R")
        self.assertEqual(vera.Time(13, 14, 15, after_sunrise=True), t)
        t = vera.Time.parse("13:14:15T")
        self.assertEqual(vera.Time(13, 14, 15, after_sunset=True), t)

class TestTimer(unittest.TestCase):

    def test_timers(self):

        s = {
            "id":2,"name":"x","type":2,"enabled":1,"days_of_week":"1,3,4",
            "time":"13:51:42" }
        t = vera.Timer.parse(s)
        u = vera.DayOfWeekTimer(2, "x", "1,3,4", vera.Time(13, 51, 42))
        self.assertEqual(t, u)

        s = {
            "id":45,"name":"zza","type":3,"enabled":1,"days_of_month":"5,9,7",
            "time":"13:51:42" }
        t = vera.Timer.parse(s)
        u = vera.DayOfMonthTimer(45, "zza", "5,9,7", vera.Time(13, 51, 42))
        self.assertEqual(t, u)        

        s = {
            "id":91,"name":"poi","type":1,"enabled":1,
            "interval":"367s" }
        t = vera.Timer.parse(s)
        u = vera.IntervalTimer(91,"poi",seconds=367)
        self.assertEqual(t, u)        

        s = {
            "id":91,"name":"poi","type":1,"enabled":1,
            "interval":"912m" }
        t = vera.Timer.parse(s)
        u = vera.IntervalTimer(91,"poi",minutes=912)
        self.assertEqual(t, u)        

        s = {
            "id":91,"name":"poi","type":1,"enabled":1,
            "interval":"36h" }
        t = vera.Timer.parse(s)
        u = vera.IntervalTimer(91,"poi",hours=36)
        self.assertEqual(t, u)

        s = {
            "id":91,"name":"poi","type":1,"enabled":1,
            "interval":"41d" }
        t = vera.Timer.parse(s)
        u = vera.IntervalTimer(91,"poi",days=41)
        self.assertEqual(t, u)

        s = {
            "id":91,"name":"poi","type":4,"enabled":1,
            "abstime":"2015-12-18 20:31:42" }
        t = vera.Timer.parse(s)
        u = vera.AbsoluteTimer(91,"poi",2015,12,18,20,31,42)
        self.assertEqual(t, u)

class TestTrigger(unittest.TestCase):

    def setUp(self):

        class MockDevice(vera.Device):
            def __init__(self):
                self.id = 56
                self.name = "Mock device"

        self.device = MockDevice()
        
        class MockVera(object):
            def __init__(self, dev):
                self.dev = dev
            def get_device_by_id(self, ignored):
                return self.dev

        self.vera = MockVera(self.device)

    def test_triggers(self):

        s = {"id": 5627,"name":"warming up","enabled":1,"arguments":[
            {"id":1,"value":12.0}],"template":8,"device":56}
        t = vera.Trigger.parse(self.vera, s)
        u = vera.Trigger(5627, "warming up", self.device, 8, [12.0])
        self.assertEqual(t,u)

        s = {"id": 5627,"name":"warming up","enabled":1,"arguments":[
            {"id":1,"value":"HeatOn"}],"template":8,"device":56,
             "start":"15:16:23","stop":"16:41:43","days_of_week":"3,5,6"}
        t = vera.Trigger.parse(self.vera, s)
        u = vera.Trigger(5627, "warming up", self.device, 8, ["HeatOn"],
                         vera.Time(15,16,23), vera.Time(16,41,43),"3,5,6")
        self.assertEqual(t,u)

class TestAction(unittest.TestCase):

    def setUp(self):

        class MockDevice(vera.Device):
            def __init__(self):
                self.id = 56
                self.name = "Mock device"

        self.device = MockDevice()
        
        class MockVera(object):
            def __init__(self, dev):
                self.dev = dev
            def get_device_by_id(self, ignored):
                return self.dev

        self.vera = MockVera(self.device)

    def test_actions(self):

        s = {"device": 56, "action": "SetCurrentSetpoint", "arguments": [
            {"name": "NewCurrentSetpoint", "value": 7.0 } ], "service":
             "urn:upnp-org:serviceId:TemperatureSetpoint1" }
        t = vera.Action.parse(self.vera, s)
        u = vera.SetpointAction(self.device, 7.0)
        self.assertEqual(t, u)
        
        s = {"device": 56, "action": "SetCurrentSetpoint", "arguments": [
            {"name": "newTargetValue", "value": 1 } ], "service":
             "urn:upnp-org:serviceId:SwitchPower1" }
        t = vera.Action.parse(self.vera, s)
        u = vera.SwitchAction(self.device, 1)
        self.assertEqual(t, u)

        s = {"device": 56, "action": "SetModeTarget", "arguments": [
            {"name": "newModeTarget", "value": "HeatOn" } ], "service":
             "urn:upnp-org:serviceId:SwitchPower1" }
        t = vera.Action.parse(self.vera, s)
        u = vera.SwitchAction(self.device, "HeatOn")
        self.assertEqual(t, u)

        s = {"device": 56, "action": "SetLoadLevelTarget", "arguments": [
            {"name": "newTargetValue", "value": 44 } ], "service":
             "urn:upnp-org:serviceId:Dimming1" }
        t = vera.Action.parse(self.vera, s)
        u = vera.DimmerAction(self.device, 44)
        self.assertEqual(t, u)

if __name__ == '__main__':
    unittest.main()

