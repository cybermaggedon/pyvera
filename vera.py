
import urllib, urllib2, json
import sys

class Vera:

    def __init__(self, host, port = 3480):
        self.host = host
        self.port = port
  
    def get_user_data(self):

        base = 'http://%s:%d' % (self.host, self.port)
        url = '%s/data_request?id=user_data&output_format=json' % (base)

        conn = urllib2.urlopen(url)
        payload = conn.read()
        payload = json.loads(payload)
        conn.close()

        return payload
  
    def get_status(self):

        base = 'http://%s:%d' % (self.host, self.port)
        url = '%s/data_request?id=status&output_format=json' % (base)

        conn = urllib2.urlopen(url)
        payload = conn.read()
        payload = json.loads(payload)
        conn.close()

        return payload
  
    def get_scene(self, id):

        base = 'http://%s:%d' % (self.host, self.port)
        url = '%s/data_request?id=scene&action=list&scene=%s&output_format=json' % (base, id)

        try:
            conn = urllib2.urlopen(url)
            payload = conn.read()
            payload = json.loads(payload)
        except:
            return None
        
        conn.close()

        return payload
    
    def delete_scene(self, id):

        base = 'http://%s:%d' % (self.host, self.port)
        url = '%s/data_request?id=scene&action=delete&scene=%s' % (base, id)

        conn = urllib2.urlopen(url)
        conn.read()
        conn.close()
  
    def create_scene(self, s):

        base = 'http://%s:%d' % (self.host, self.port)

        s = json.dumps(s)

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
        
        url = '%s/data_request?id=scene&action=create&json=%s' % (base, s)

        conn = urllib2.urlopen(url)
        conn.read()
        conn.close()
