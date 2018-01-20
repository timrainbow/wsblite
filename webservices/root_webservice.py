
import logging

from webcommon.base_webservice import BaseWebService

WEB_SERVICE_CONFIG = {BaseWebService.CONF_ITM_NAME: 'Root',
                         BaseWebService.CONF_ITM_ENABLED: 'true',
                         BaseWebService.CONF_ITM_OWNED_URLS: 
                             {'/': 
                                 {BaseWebService.CONF_ITM_ALLOW_METH : ['GET'],
                                  BaseWebService.CONF_ITM_FULL_MATCH_ONLY : 'true'}
                             }
                     }


class RootWebService(BaseWebService):
    """ Example RootWebService which handles requests to the top level. This
        example simply displays links to the currently loaded and running 
        WebServices.
    """
    
    def __init__(self):
        super().__init__(WEB_SERVICE_CONFIG)
        self.html_body = ''
    
    def perform_client_request(self, method, path, headers, payload_type, payload_content):
        return self.ServiceResponse(payload=self.html_body)
    
    def initialise(self, web_services_loaded):
        """ At initialisation we get a sneaky look at other web services running
            so this is when we will create links to them ready for when the client
            requests the root url.
        """
        for web_service in web_services_loaded:
            if web_service.service_name == self.service_name:
                # We don't want to provide a link to ourself (the root url), so skip to the next web service.
                continue

            self.html_body += '<h2>' + web_service.service_name + '</h2><ul>'
            for owned_url in web_service.get_allowed_http_methods()['GET']:
                self.html_body += '<li><a href="' + owned_url + '">' + owned_url  +'</a><br></li>'
            self.html_body += '</ul>'

    
    def start(self):
        logging.info('RootWebService Start')
        logging.info(self.html_body)
    
    def stop(self):
        logging.info('RootWebService Stop')