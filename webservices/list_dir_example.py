
import os
import logging

from webservices.common.base_webservice import BaseWebService

WEB_SERVICE_CONFIG = {BaseWebService.CONF_ITM_NAME: 'Example WebService',
                         BaseWebService.CONF_ITM_ENABLED: 'true',
                         BaseWebService.CONF_ITM_OWNED_URLS: 
                             {'/list_directory': 
                                 {BaseWebService.CONF_ITM_ALLOW_METH : ['GET']}
                             }
                     }


class ListDirWebService(BaseWebService):
    """ Example WebService which inherits from BaseWebService because it doesn't
        need to maintain a running concurrent background process to interact with
        when the client request comes in. Another example to inherit from 
        BaseWebService is if you can perform some calculation or operation externally
        on the client's request. 
        
        This example returns a list of files
        and directories in the current working directory. 
    """
    def __init__(self):
        super().__init__(WEB_SERVICE_CONFIG)
    
    def perform_client_request(self, method, path, payload_type, payload_content):
        """ Return the contents of the current working directory when a client 
            request comes in for a url path we registered for.
        """
        response = "<h1>Contents of current working directory:</h1>"
        response += '<br>'.join(os.listdir(os.curdir))
        return self.ServiceResponse(payload=response)
    
    def start(self):
        logging.info('ListDirWebService Start')
    
    def stop(self):
        logging.info('ListDirWebService Stop')