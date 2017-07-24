# coding=utf-8
__author__ = 'lxn3032'


import threading
import uuid

from .object_proxy import RpcObjectProxy
from .exceptions import RpcException, RpcRemoteException, RpcTimeoutException
from .utils.promise import Promise


class RpcClient(object):
    def __init__(self, auto_connect=True):
        self._timeout = 15
        self._resp_events = {}  # rpc request id -> threading.Event
        self._responses = {}  # reqid -> resp
        self._responses_mutex = threading.Lock()
        self._evaluated_count = 0
        self.transport = self.initialize_transport()

        if auto_connect:
            self.connect()

    def initialize_transport(self):
        raise NotImplementedError

    def connect(self):
        self.transport.connect()

    def disconnect(self):
        self.transport.disconnect()

    @property
    def connected(self):
        return bool(self.transport is not None and self.transport.connected)

    def remote(self, uri):
        return RpcObjectProxy(uri, self)

    def evaluate(self, obj_proxy, wait_for_response=True, out_response=None, on_response=None):
        # TODO: evaluate 的流程和response handling的流程要分离
        if not isinstance(obj_proxy, RpcObjectProxy):
            raise RuntimeError('Only RpcObjectProxy object can be evaluated. got {}'.format(repr(obj_proxy)))
        if not self.connected:
            raise RuntimeError('Rpc client not connected! Please call connect() first.')

        result_is_intermidiate_obj = False
        intermidiate_obj = None
        if not obj_proxy._evaluated__:
            self._evaluated_count += 1
            evt = threading.Event()
            if wait_for_response:
                reqid = str(uuid.uuid4())
                self._resp_events[reqid] = evt
            else:
                reqid = ''

            # emit request
            if on_response:
                self.transport.add_response_callback(reqid, on_response)
            self.transport.send({'id': reqid, 'uri': obj_proxy._uri__, 'method': obj_proxy._invocation_path__})

            if wait_for_response and not on_response:
                success = evt.wait(timeout=self._timeout)
                if not success:
                    raise RpcTimeoutException(self.transport.session_id, reqid, obj_proxy._uri__, obj_proxy._invocation_path__)
                resp = self.get_response(reqid)
                if out_response is not None:
                    out_response.update(resp)
                if not resp:
                    raise RpcException(self.transport.session_id, reqid, 'Remote responses nothing!')
                if 'errors' in resp:
                    raise RpcRemoteException(resp)

                intermidiate_uri = resp.get('uri')
                if intermidiate_uri:
                    result_is_intermidiate_obj = True
                    intermidiate_obj = RpcObjectProxy(intermidiate_uri, self)
                    intermidiate_obj._evaluated__ = True
                    intermidiate_obj._evaluated_value__ = resp.get('result')
                    intermidiate_obj._is_intermediate_uri__ = True

                obj_proxy._evaluated_value__ = resp.get('result')
            obj_proxy._evaluated__ = True

        if result_is_intermidiate_obj:
            return intermidiate_obj
        elif obj_proxy._is_intermediate_uri__:
            return obj_proxy
        else:
            return obj_proxy._evaluated_value__

    def resolve(self, obj_proxy):
        @Promise
        def prom(resv, reject):
            def on_response(resp):
                if not resp:
                    raise RpcException(self.transport.session_id, '', 'Remote responses nothing!')
                if 'errors' in resp:
                    raise RpcRemoteException(resp)

                intermidiate_uri = resp.get('uri')
                if intermidiate_uri:
                    intermidiate_obj = RpcObjectProxy(intermidiate_uri, self)
                    intermidiate_obj._evaluated__ = True
                    intermidiate_obj._evaluated_value__ = resp.get('result')
                    intermidiate_obj._is_intermediate_uri__ = True
                    resv(intermidiate_obj)
                else:
                    resv(resp.get('result'))

            try:
                self.evaluate(obj_proxy, on_response=on_response)
            except RpcException as e:
                reject(e)

        return prom

    def invoke(self, object_proxy, method, args=()):
        @Promise
        def prom(resv, reject):
            def on_response(resp):
                if not resp:
                    raise RpcException(self.transport.session_id, '', 'Remote responses nothing!')
                if 'errors' in resp:
                    raise RpcRemoteException(resp)

                intermidiate_uri = resp.get('uri')
                if intermidiate_uri:
                    intermidiate_obj = RpcObjectProxy(intermidiate_uri, self)
                    intermidiate_obj._evaluated__ = True
                    intermidiate_obj._evaluated_value__ = resp.get('result')
                    intermidiate_obj._is_intermediate_uri__ = True
                    resv(intermidiate_obj)
                else:
                    resv(resp.get('result'))

            try:
                new_proxy = getattr(object_proxy, method).__call_no_evaluate__(*args)
                self.evaluate(new_proxy, on_response=on_response)
            except RpcException as e:
                reject(e)

        return prom

    def put_response(self, resp):
        with self._responses_mutex:
            reqid = resp['id']
            self._responses[reqid] = resp
            evt = self._resp_events.pop(reqid, None)
            if evt:
                evt.set()

    def get_response(self, reqid):
        return self._responses.pop(reqid, None)

    def reset_evaluation_counter(self):
        self._evaluated_count = 0

    def set_timeout(self, t):
        self._timeout = t

    def get_timeout(self):
        return self._timeout
