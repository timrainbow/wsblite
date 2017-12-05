
import logging

from webcommon.base_webservice import BaseWebService

WEB_SERVICE_CONFIG = {BaseWebService.CONF_ITM_NAME: 'Root',
                         BaseWebService.CONF_ITM_ENABLED: 'true',
                         BaseWebService.CONF_ITM_OWNED_URLS: 
                             {'/': 
                                 {BaseWebService.CONF_ITM_ALLOW_METH : ['GET']}
                             }
                     }


class RootWebService(BaseWebService):
    """ Example RootWebService which handles requests to the top level. This
        example simply displays links to the currently loaded and running 
        WebServices.
    """
    
    def __init__(self):
        super().__init__(WEB_SERVICE_CONFIG)
        self.links = list()
    
    def perform_client_request(self, method, path, headers, payload_type, payload_content):
        return self.ServiceResponse(payload='<br>'.join(self.links))
    
    def initialise(self, web_service_lookup):
        """ At initialisation we get a sneaky look at other web services running
            so this is when we will create links to them ready for when the client
            requests
        """
        for url, web_service in web_service_lookup['GET'].items():
            link = '<a href="' + url + '">' + web_service.service_name  +'</a>'
            self.links.append(link)
    
    def start(self):
        logging.info('RootWebService Start')
        logging.info(self.links)
    
    def stop(self):
        logging.info('RootWebService Stop')