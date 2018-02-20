import hmac
import base64
import urllib.parse
import urllib.request
import time

class DeviceClient():
    """ 
        Client for Azure IoT Hub REST API 
        https://msdn.microsoft.com/en-us/library/mt590785.aspx
    """
    _API_VERSION = 'api-version=2016-11-14'
    _HEADER_AUTHORIZATION = 'Authorization'

    """
        iot_hub_name - name of your Azure IoT Hub
        device_name - name of your device
        key - security key for your device
    """
    def __init__(self, iot_hub_name, device_name, key):
        self._iot_hub_name = iot_hub_name
        self._device_name = device_name
        self._key = key

        self._base_url = 'https://' + \
                        self._iot_hub_name + \
                        '.azure-devices.net/devices/' + \
                        self._device_name + \
                        '/messages/'

        self._url_to_sign = self._iot_hub_name + \
                        '.azure-devices.net/devices/' + \
                        self._device_name

    """
        Creates Shared Access Signature. Run before another funstions
        timeout - expiration in seconds
    """
    def create_sas(self, timeout):
        urlToSign = urllib.parse.quote(self._url_to_sign, safe='') 
        
        # current time +10 minutes
        timestamp = int(time.time()) + timeout

        h = hmac.new(base64.b64decode(self._key), 
                    msg = "{0}\n{1}".format(urlToSign, timestamp).encode('utf-8'),
                    digestmod = 'sha256')

        self._sas = "SharedAccessSignature sr={0}&sig={1}&se={2}".format(urlToSign, 
                    urllib.parse.quote(base64.b64encode(h.digest()), safe = ''),
                    timestamp)

        return self._sas

    """
        Sends message
        message - message to be send

        Returns HTTP response code. 204 is OK.
        https://msdn.microsoft.com/en-us/library/mt590784.aspx
    """
    def send(self, message):
        headers = {
            self._HEADER_AUTHORIZATION : self._sas,
            'Content-Type' : 'application/json'
            }

        req = urllib.request.Request(self._base_url + 'events?' + self._API_VERSION,
                                     message,
                                     headers,
                                     method = 'POST')

        return_code = 0

        with urllib.request.urlopen(req) as f:
            return_code = f.code

        return return_code

    """
        Reads first message in queue

        Returns:
        message['headers'] - all response headers
        message['etag'] - message id, you need this for complete, reject and abandon
        message['body'] - message content
        message['response_code'] - HTTP response code

        https://msdn.microsoft.com/en-us/library/mt590786.aspx
    """

    def read_message(self):
        headers = {
            self._HEADER_AUTHORIZATION : self._sas,
            }

        req = urllib.request.Request(self._base_url + 'devicebound?' + self._API_VERSION,
                                    headers = headers,
                                    method = 'GET')

        message = {}

        with urllib.request.urlopen(req) as f:
            # Process headers
            message['headers'] =  f.info()
            message['etag'] = ''
            if f.info()['ETag'] != None:
                message['etag'] = f.info()['ETag'].strip('"')
            
            # message
            message['body'] = f.read().decode('utf-8')
            message['response_code'] = f.code

        return message

    """
        Completes a cloud-to-device message.
        id - use message['etag'] from read_message function
        
        Returns HTTP response code. 204 is OK.
        https://msdn.microsoft.com/en-us/library/mt605155.aspx
    """
    def complete_message(self, id):
        headers = {
            self._HEADER_AUTHORIZATION : self._sas,
            }

        req = urllib.request.Request(self._base_url + 'devicebound/' + id + '?' + self._API_VERSION,
                                    headers = headers,
                                    method = 'DELETE')

        return_code = 0

        with urllib.request.urlopen(req) as f:
            return_code = f.code

        return return_code
    
    """
        Completes a cloud-to-device message.
        id - use message['etag'] from read_message function
        
        Returns HTTP response code. 204 is OK.

        https://msdn.microsoft.com/en-us/library/mt590787.aspx
    """
    def reject_message(self, id):
        headers = {
                        self._HEADER_AUTHORIZATION : self._sas,
                    }

        req = urllib.request.Request(self._base_url + 'devicebound/' + id + '?reject&' + self._API_VERSION,
                                headers = headers,
                                method = 'DELETE')

        return_code = 0

        with urllib.request.urlopen(req) as f:
            return_code = f.code

        return return_code

    """
        Abandon a cloud-to-device message
        id - use message['etag'] from read_message function
        
        Returns HTTP response code. 204 is OK.

        https://msdn.microsoft.com/en-us/library/mt590788.aspx
    """
    def abandon_message(self, id):
        headers = {
                        self._HEADER_AUTHORIZATION : self._sas,
                    }

        req = urllib.request.Request(self._base_url + 'devicebound/' + id + '/abandon?' + self._API_VERSION,
                                '',
                                headers,
                                method = 'POST')

        return_code = 0

        with urllib.request.urlopen(req) as f:
            return_code = f.code

        return return_code
