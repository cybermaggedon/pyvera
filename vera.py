
import urllib, urllib2, json
import sys
import sha
import base64
import httplib
import time
import requests

class Vera:

    def not_empty(self, payload):
        
        if (payload == ""):
            return False

        return True

    def get(self, path):
        raise RuntimeError("Not implemented")

    def get_user_data(self):

        payload = self.get('data_request?id=user_data&output_format=json')
        return payload
  
    def get_sdata(self):

        payload = self.get('data_request?id=sdata&output_format=json')
        return payload
  
    def get_status(self):

        payload = self.get('data_request?id=status&output_format=json')
        return payload
  
    def get_scene(self, id):

        payload = self.get('data_request?id=scene&action=list&scene=%s&output_format=json' % id)
        return payload
    
    def delete_scene(self, id):

        payload = self.get('data_request?id=scene&action=delete&scene=%s' % id)
        return payload
  
    def create_scene(self, s):

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
        
        payload = self.get('data_request?id=scene&action=create&json=%s' % s)
        return payload

class VeraLocal(Vera):

    def __init__(self, host, port = 3480):
        self.host = host
        self.port = port

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

        url = "https://vera-us-oem-autha11.mios.com/autha/auth/username/%s?SHA1Password=%s&PK_Oem=1" % (user.lower(), sha1p)

        response = self.session.get(url).json()

        server_account = response["Server_Account"]
        auth_token = response["Identity"]
        auth_sig = response["IdentitySignature"]

        # Get session token for authd11
        headers = {"MMSAuth": auth_token, "MMSAuthSig": auth_sig}

        url = "https://vera-us-oem-authd11.mios.com/info/session/token"
        session_token = self.session.get(url, headers=headers).text

        # Get device location
        headers = { "MMSSession": session_token }

        url = "https://vera-us-oem-authd11.mios.com/locator/locator/locator"
        devices = self.session.get(url, headers=headers).json()

        server_device = None

        for i in devices["Devices"]:
            if i["PK_Device"] == device:
                server_device = i["Server_Device"]

        if server_device == None:
            raise RuntimeError, "Device %s not known.\n" % device
                
        sys.stderr.write("Server device: %s\n" % server_device)

        # Get session token on server_device
        headers = {"MMSAuth": auth_token, "MMSAuthSig": auth_sig}

        url = "https://" + server_device + "/info/session/token"
        session_token = self.session.get(url, headers=headers).text

        # Get server_relay
        headers = { "MMSSession": session_token }

        url = "https://" + server_device + "/device/device/device/" + str(device)

        relay_info = self.session.get(url, headers=headers).json()

        self.relay = relay_info["Server_Relay"]

        sys.stderr.write("Server relay: %s\n" % self.relay)

        # Get session token on server_relay

        headers = {"MMSAuth": auth_token, "MMSAuthSig": auth_sig}
        url = "https://" + self.relay + "/info/session/token"
        self.session_token = self.session.get(url, headers=headers).text

    def get(self, path):

        headers = { "MMSSession": self.session_token }

        url = "https://%s/relay/relay/relay/device/%s/port_3480/%s" % (self.relay, str(self.device), path)

        response = requests.get(url, headers=headers)

        try: 
            return response.json()
        except:
            pass

        return response.text
        
