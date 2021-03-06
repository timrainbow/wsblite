import http.server
import urllib.parse
import json
import os
import logging
import socketserver

from threading import Thread
from webcommon.base_webservice import BaseWebService, HTTPStatus


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """ Allows support for asynchronous behaviour (a thread per request)
    """
    allow_reuse_address = True
    daemon_threads = True


class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """ The HTTPRequestHandler acts as the view to the client's requests and is
        the first to be notified. On the client's request, the HTTPRequestHandler
        extracts the required information and passes it to the WebServiceController
    """
    
    @classmethod
    def set_controller(cls, controller):
        cls.controller = controller
    
    @classmethod
    def parse_response(self, raw_response):
        return None  
         
    def get_payload(self):
        content_len = int(self.headers.get('content-length', 0))
        raw_message_body = self.rfile.read(content_len)
        
        content_type = self.headers.get('content-type', '')
        message_body = None
        if content_type == 'application/json':
            message_body = json.loads(raw_message_body.decode())
        else:
            message_body = urllib.parse.unquote_plus(raw_message_body.decode())
        
        return (content_type, message_body)
    
    def do_GET(self):
        """ Serves a GET request.
        """
        controller = HTTPRequestHandler.controller
        
        if 'favicon.ico' in self.path:
            favicon_path = os.path.join(controller._resource_dir, 'favicon.ico')
            if os.path.exists(favicon_path):
                img_data = open(favicon_path, 'rb').read()
                img_resp = BaseWebService.ServiceResponse(payload=img_data,
                                                          add_html_wrapper=False,
                                                          content_type='image/x-icon')
                self.__handle_result(img_resp)
            else:
                logging.info('Client requested favicon but nothing found here: ' + favicon_path)
        else:
            
            result = controller.perform_client_request(self, 'GET', self.path, self.headers)
            self.__handle_result(result)
            
    def do_POST(self):
        """ Serves a POST request.
        """
        (payload_type, payload_content) = self.get_payload()
        
        controller = HTTPRequestHandler.controller
        result = controller.perform_client_request(self, 'POST', self.path, self.headers, payload_type,
                                                   payload_content)
        self.__handle_result(result)
        
    def do_PUT(self):
        """ Serves a PUT request.
        """
        (payload_type, payload_content) = self.get_payload()
        
        controller = HTTPRequestHandler.controller
        result = controller.perform_client_request(self, 'PUT', self.path, self.headers, payload_type,
                                                   payload_content)
        self.__handle_result(result)
        
    def do_DELETE(self):
        """ Serves a DELETE request.
        """
        controller = HTTPRequestHandler.controller
        result = controller.perform_client_request(self, 'DELETE', self.path, self.headers)
        self.__handle_result(result)
        
            
    def __handle_result(self, result):
        self.__send_response(result)
            
        
    def __send_response(self, service_resp):
        """ Sends a HTTP response back to the user with a format defined by the
            caller. If service_resp is None then nothing is sent back to the client.
        """
        if service_resp:
            self.send_response(service_resp.resp_code)
            if service_resp.payload:
                self.send_header("Content-type", service_resp.content_type)
                self.send_header("Content-Length", len(service_resp.payload))

            # Send any additional headers the user has specifically requested.
            for header_key, header_value in service_resp.add_headers.items():
                self.send_header(header_key, header_value)

            self.end_headers()

            self.wfile.write(service_resp.payload)


class WebServiceController(object):
    """ The WebServiceController loads the imported web services and waits for 
        the HTTPRequestHandler to notify it of an incoming request (with info).
        The WebServiceController also ensures the HTTP server is running and
        generally manages the other processes and threads involved.
    """
    
    
    def __init__(self, port, web_service_classes,
                 resource_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                                           'resources'))):
        """ Instantiates all web services and also adds them ta a lookup to allow
            rapid searches for the correct web service to handle incoming requests.
        """
        
        self._port                = port
        self._loaded_web_services = self.__instantiate_web_services(web_service_classes)
        self._web_service_lookup  = self.__create_web_service_lookup(self._loaded_web_services)
        self._server_address      = None
        self._resource_dir        = resource_dir
        
        self.__server_thread  = None
        self.__server         = None
        
    def start(self):
        """ Starts the controller which in turn starts all of the web services
            and then finally the HTTP server.
        """
        for web_service in self._loaded_web_services:
            # Initialise all services to make them aware of other services
            # running before they are actually started.
            web_service.initialise(self._loaded_web_services)
            
        for web_service in self._loaded_web_services:
            web_service.start()
            
        self.__start_server()
        
    def stop(self):
        """ Stops the controller which stops the HTTP server first and then
            finally stops the web services.
        """
        self.__stop_server()
        for web_service in self._loaded_web_services:
            web_service.stop()
        
    def is_server_running(self):
        return self.__server_thread.isAlive()
    
    def wait_here_until_server_thread_stops(self):
        self.__server_thread.join()
    
    def parse_response(self, raw_response):
        return self.__server.RequestHandlerClass.parse_response(raw_response)
    
    def perform_client_request(self, handler, method, path, headers, payload_type=None, payload_content=None):
        """ Called when the HTTPRequestHandler receives a request from a client.
            This is where the controller looks to see which web service should
            handle the client's request. 
        """

        if '//' in path:
            # Double slash in the URL path should give a BAD REQUEST
            return BaseWebService.ServiceResponse(resp_code=HTTPStatus.BAD_REQUEST)

        selected_web_service = self.__get_web_service_that_owns_path(path, self._web_service_lookup[method])

        if selected_web_service:
            if selected_web_service.auth_all_enabled:
                auth_passed = selected_web_service.check_authentication(path, headers)
            else:
                logging.info('Authentication is disabled for all owned urls for: ' + selected_web_service.service_name)
                auth_passed = True

            if not auth_passed:
                return selected_web_service.request_authentication(realm=selected_web_service.service_name)

            return selected_web_service.perform_client_request(handler, method, path, headers, payload_type,
                                                               payload_content)
        else:
            return BaseWebService.ServiceResponse(resp_code=HTTPStatus.NOT_FOUND)

    def __get_web_service_that_owns_path(self, path, web_service_candidates, path_is_trimmed=False):
        """ Gets the web service that owns the path. If no web service owns the given path then the next available web
            service that comes close is returned instead. For example if a web service owns http://example.com/api/ then
            anything under that path which isn't specified explicitly will return that web service such as
            http://example.com/api/test or http://example.com/api/some/path/under/this/one.
        """
        if path in web_service_candidates:
            selected_web_service = web_service_candidates[path]

            if path_is_trimmed:
                # Only return the web service if it allows the client to not provide an exact match
                if not selected_web_service.owned_path_must_be_exact(path):
                    return selected_web_service
            else:
                return selected_web_service

        if path != '/':
            return self.__get_web_service_that_owns_path(os.path.dirname(path), web_service_candidates,
                                                         path_is_trimmed=True)
        else:
            return None

    def __instantiate_web_services(self, web_service_classes):
        """ Default initialises all of the WebServices that have been imported.
        """
        web_services = list()
        for web_service in web_service_classes:
            instantiated_web_service = web_service()
            if instantiated_web_service.enabled:
                web_services.append(instantiated_web_service)
        return web_services
    
    def __create_web_service_lookup(self, loaded_web_services):
        """ Creates a fast lookup using a list of loaded (instantiated) web
            services.
        """
        lookup = { 'GET' : dict(), 'POST' : dict(), 'PUT' : dict(), 'DELETE' : dict() }
        for web_service in loaded_web_services:
            
            allowed_methods = web_service.get_allowed_http_methods()
            for method, url_list in allowed_methods.items():
                for url in url_list:
                    lookup[method][url] = web_service
            
        return lookup
            
    
    def __server_run_thread(self):
        """ Blocking thread call which serves the HTTP server.
        """
        
        try:
            logging.info('Starting Server')
            self.__server.serve_forever()
            
            logging.debug('Confirmed, Server shutdown')
        except:
            logging.error('Failed to start server')
        finally:
            self.__server.server_close()
    
    def __start_server(self):
        """ Starts the HTTP server on the configured port.
        """
        self._server_address = ('', self._port)
        self.__server = ThreadedHTTPServer(self._server_address, HTTPRequestHandler)
        # Set ourselves onto the server so it can callback to us
        self.__server.RequestHandlerClass.set_controller(self)
        sa = self.__server.socket.getsockname()
        logging.info("Serving HTTP on port " + str(sa[1]))
        
        self.__server_thread = Thread(target=self.__server_run_thread)
        self.__server_thread.start()
            
    def __stop_server(self):
        """ Stops the HTTP server.
        """
        logging.info('Shutting down server...')
        self.__server.shutdown()
        self.__server_thread.join()
        logging.info('Server shutdown')

