
import logging

from random import randint
from webcommon.background_webservice import BaseWebService, BaseBackgroundWebService
from time import sleep

WEB_SERVICE_CONFIG = {BaseWebService.CONF_ITM_NAME: 'Random Number Generator',
                         BaseWebService.CONF_ITM_ENABLED: 'true',
                         BaseWebService.CONF_ITM_OWNED_URLS:
                             {'/random_number':
                                 {BaseWebService.CONF_ITM_ALLOW_METH : ['GET'],
                                  BaseWebService.CONF_ITM_FULL_MATCH_ONLY: 'true'}
                             }
                     }

class RandomNumWebService(BaseBackgroundWebService):
    """ Example WebService which inherits from BaseBackgroundWebService. This allows
        you to maintain a running concurrent background process to interact with
        when the client request comes in. You can also (as in this example) 
        perform some operation every couple of seconds and the client request
        just returns the latest result.
        
        If you need to stand up another process
        which you intend to interact with when a client requests your service or
        you need to perform the same operation constantly and return the latest
        result then your WebService should inherit from BaseBackgroundWebService.
        
        This example generates a random number from 1-100 every few seconds and 
        the latest result is returned to the client on request. 
    """

    class RandomNumBackgroundProcess(BaseBackgroundWebService.BaseBackgroundProcess):
        """ Example background process to carry out work without requiring 
            a client's request first. Your background process should inherit
            from BaseBackgroundProcess.
        """

        # This is the message we pass from the WebService to the background process.
        REQUEST_RANDOM_NUM = 'latest_random_number'

        def __init__(self, receive_queue, send_queue):
            super().__init__(receive_queue, send_queue)

            self.__random_number_generated = None


        def initialise(self):
            """ Any setup work or initialising member variables needs to happen in
                this method.
            """
            self.__random_number_generated = 0

        def loop(self):
            """ This method generates a new random number and is called as soon
                as it exits. Allowing the method to exit before it is re-called
                gives the WebService a chance to see if it has been told to stop
                and therefore blocking here means it may be terminated without
                notice.
            """
            self.__random_number_generated = randint(1, 100)
            logging.info("Latest random number: " + str(self.__random_number_generated))
            sleep(5)

        def deinitialise(self):
            """ Any resources owned can be released here before the process exits
            """
            self.__random_number_generated = 0


        def handle_request(self, message_received):
            """ This is called indirectly when the WebService makes a request
                to this background process. Here we check that the request is
                for a random number and pass back the latest number generated.
            """
            if message_received == self.REQUEST_RANDOM_NUM:
                return self.__random_number_generated
            else:
                return None



    def __init__(self):
        """ When we __init__ in a subclass derived from BaseBackgroundWebService,
            we must pass the background process class we intend to run. This
            class should inherit from BaseBackgroundProcess.
        """
        super().__init__(WEB_SERVICE_CONFIG, self.RandomNumBackgroundProcess)


    def perform_client_request(self, handler, method, path, headers, payload_type, payload_content):
        """ When a client requests for a random number, we inform the background
            process of this request and block until we get the result for the 
            client. We pass a message to the background process so it knows what
            we're asking for. We define the message and handle it in the
            background process with handle_request so the message can be anything
            so long as we handle it on the other side.
        """
        answer = self.request(self.RandomNumBackgroundProcess.REQUEST_RANDOM_NUM)

        return self.ServiceResponse(payload=str(answer))

    def start(self):
        """ You must call super().start() if you override this method as it is
            responsible for running your background process.
        """
        super().start()
        logging.info('RandomNumWebService Start')

    def stop(self):
        """ You must call super().stop() if you override this method as it is
            responsible for stopping your background process.
        """
        super().stop()
        logging.info('RandomNumWebService Stop')
