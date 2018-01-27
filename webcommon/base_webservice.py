
import logging
import base64
import os
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
    CONF_ITM_ENABLED    = 'service_enabled'

    # Owned URLs
    CONF_ITM_ALLOW_METH      = 'allowed_methods'
    CONF_ITM_FULL_MATCH_ONLY = 'full_match_only'

    # Auth config items
    CONF_ITM_AUTH_ALL_ENABLED    = 'auth_all_enabled'

    CONF_ITM_AUTH_BASIC_ENABLED  = 'auth_basic_enabled'
    CONF_ITM_AUTH_USERNAME       = 'auth_username'
    CONF_ITM_AUTH_PASSWORD       = 'auth_password'
    
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

        # Authentication
        if self.CONF_ITM_AUTH_ALL_ENABLED in config:
            if config[self.CONF_ITM_AUTH_ALL_ENABLED].lower() == 'true':
                self.auth_all_enabled = True
            else:
                self.auth_all_enabled = False
        else:
            # Default to enabled to honour auth info if entered for a given owned url
            self.auth_all_enabled = True

        
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
    
    def perform_client_request(self, handler, method, path, headers, payload_type, payload_content):
        """ Called when a client performs a request with a url path that matches
            the one this WebService registered. The HTTP method used by the client
            must also match the allowed methods by this WebService.
        """
        return None

    def request_authentication(self, realm):
        """ Populate a response to send back to the client requesting authentication details to proceed.
        """
        headers_to_add = {'WWW-Authenticate': 'Basic realm="' + realm + '"'}
        return self.ServiceResponse(resp_code=HTTPStatus.UNAUTHORIZED, add_headers=headers_to_add)
     
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

    def check_authentication(self, path, headers):
        """ Checks if the particular url owned by this web service requires authentication or not. If it does, it will
            check the Authorization header against the stored username and password. Returns True if the client validated
            (either by supplying the right credentials or if authentication is disabled for the url being accessed).
        """
        logging.debug('Verifying authentication requirements of owned urls are met')

        url_config = self.__get_url_config(path)

        check_credentials = True

        if self.CONF_ITM_AUTH_BASIC_ENABLED in url_config:
            if url_config[self.CONF_ITM_AUTH_BASIC_ENABLED].lower() == 'true':
                check_credentials = True
            else:
                # Auth specifically disabled in config for this path
                check_credentials = False
        elif self.CONF_ITM_AUTH_USERNAME in url_config and self.CONF_ITM_AUTH_PASSWORD in url_config:
            if url_config[self.CONF_ITM_AUTH_USERNAME] and url_config[self.CONF_ITM_AUTH_PASSWORD]:
                logging.debug('Authentication not specifically enabled but a username and password have been supplied - '
                             'assuming authentication required (provide ' + self.CONF_ITM_AUTH_BASIC_ENABLED + ' to '
                             'silence this message)')
                check_credentials = True
        else:
            check_credentials = False

        auth_passed = False
        if check_credentials:
            logging.debug('Authentication required')
            auth_header = headers.get('Authorization')
            if auth_header:
                encoded_credentials = self.get_encoded_auth_credentials(path)
                if 'Basic ' + encoded_credentials == auth_header:
                    logging.info('Authentication passed')
                    auth_passed =  True
                else:
                    logging.info('Authentication failed - wrong username or password')
                    return False
            else:
                auth_passed = False
        else:
            logging.debug('Authentication not needed')
            auth_passed = True

        return auth_passed

    def get_encoded_auth_credentials(self, path):
        """ Returns the credentials encoded for basic web authentication i.e. Basic username:password (as base64 encoded)
        """
        url_config = self.__get_url_config(path)

        username = url_config[self.CONF_ITM_AUTH_USERNAME]
        password = url_config[self.CONF_ITM_AUTH_PASSWORD]

        credentials = username + ':' + password

        return base64.b64encode(credentials.encode()).decode()

    def owned_path_must_be_exact(self, path):
        """ Checks if this web service only allows clients to access the given path if provided exactly i.e. it cannot
            have extra levels underneath it.
        """
        path_must_be_exact = False

        url_config = self.__get_url_config(path)

        if url_config and BaseWebService.CONF_ITM_FULL_MATCH_ONLY in url_config:
            if url_config[BaseWebService.CONF_ITM_FULL_MATCH_ONLY].lower() == 'true':
                path_must_be_exact = True

        return path_must_be_exact

    def __get_url_config(self, path):
        """ Gets the url config for a given url path. If the exact path doesn't match then the closest web service to it
            is returned - if it contains a higher level path.
        """
        if path in self.owned_urls:
            return self.owned_urls[path]
        elif path != '/':
            return self.__get_url_config(os.path.dirname(path))
        else:
            return None
