# coding=utf-8
__author__ = 'lxn3032'


import json
import requests


from hrpc.transport import Transport


class HttpTransport(Transport):
    def __init__(self, endpoint, client):
        super(HttpTransport, self).__init__(endpoint, client)
        self.connect()

    def send(self, req):
        req['session_id'] = self.session_id
        r = requests.post(self.endpoint, data=json.dumps(req), headers={'Content-Type': 'application/json'})
        self.rpc_client.put_response(r.json())

    def connect(self):
        self.connected = True

    def disconnect(self):
        pass

    def ping(self):
        try:
            r = requests.post(self.endpoint, data='', timeout=1)
            return True
        except:
            return False
