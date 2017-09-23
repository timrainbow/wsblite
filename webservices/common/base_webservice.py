
from http import HTTPStatus

class BaseWebService(object):
    """ The BaseWebService contains all of the boilerplate code common to all
        derived WebServices so that those services can just worry about their 
        specific operation.
        
        Inherit from this if your WebService can perform the logic required at 
        the time it is requested by the client.
    """
    
    class ServiceResponse(object):
        """ Encapsulates the response back to the client such as the data to send
            back as well as the HTTP response code, content type etc.
        """
        
        def __init__(self, payload=None, resp_code=HTTPStatus.OK, add_headers=None,
                     add_html_wrapper=True, content_type='text/html'):
            """ Creates a ServiceResponse determined by the data passed to it
                at initialisation. For example, passing no payload means one is
                generated automatically from the HTTP response code given.
            """
            # TODO: Refactor this class, it's a bit messy
             
            # Payload
            if payload != None:
                self.payload = payload
            else:
                self.payload = ''
                
            # Response Code
            self.resp_code = resp_code
            
            if not self.payload:
                self.payload = self.resp_code.phrase + ' - ' + self.resp_code.description
                
            if add_html_wrapper:
                self.payload = "<html>" + self.payload + "</html>"
            if 'text/html' == content_type:
                self.payload = self.payload.encode()
            
            
            self.content_type = content_type
            
            # Response Code
            self.resp_code = resp_code
            
            if not self.payload:
                self.payload = self.resp_code[1] + ' - ' + self.resp_code[2]
            
            # Headers
            if add_headers:
                self.add_headers = add_headers
            else:
                self.add_headers = dict()
                
    
    # Configuration item keys used to drill down into the WebService config.
    CONF_ITM_NAME       = 'service_name'
    CONF_ITM_OWNED_URLS = 'owned_urls'
    CONF_ITM_ENABLED    = 'enabled'
    CONF_ITM_ALLOW_METH = 'allowed_methods'
    
    def __init__(self, web_service_config):
        self.__web_service_config = web_service_config
        
        self.populate_web_service_with_config(self.__web_service_config)
        
        
    def populate_web_service_with_config(self, config):
        """ Populates the WebService with a given config
        """
        if config[self.CONF_ITM_ENABLED].lower() == 'true':
            self.enabled = True
        else:
            self.enabled = False
            
        self.service_name = config[self.CONF_ITM_NAME]
        
        self.owned_urls = config[self.CONF_ITM_OWNED_URLS]
        
    def initialise(self, web_service_lookup):
        """ This method is called just before the start method. The lookup created
            by the controller is passed in order for the WebService to see what
            other services are enabled.
        """
        pass
        
    def start(self):
        """ This method is called after the initialise method. Any final setup
            operations can be placed here.
        """
        pass
    
    def stop(self):
        """ This method is called when the service should stop. Place cleanup
            operations here but be careful that they do not take too long - the
            controller may terminate the service if it takes too long to stop.
        """
        pass
    
    def perform_client_request(self, method, path, payload_type, payload_content):
        """ Called when a client performs a request with a url path that matches
            the one this WebService registered. The HTTP method used by the client
            must also match the allowed methods by this WebService.
        """
        return None

#     
    def get_allowed_http_methods(self):
        """ Creates a dictionary holding the HTTP methods as keys with a list 
            of url paths that this WebService owns as values.
        """
        allowed_http_methods = { 'GET' : list(), 'POST' : list(), 'PUT' : list(), 'DELETE' : list() }
        for url, url_config in self.owned_urls.items():
            allowed_for_this_url = url_config[self.CONF_ITM_ALLOW_METH]
            for http_method in allowed_for_this_url:
                allowed_http_methods[http_method].append(url)
            
        
        return allowed_http_methods

    
    
    