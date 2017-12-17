
import multiprocessing
import threading
import queue
import logging

from time import sleep
from webcommon.base_webservice import BaseWebService


class BaseBackgroundWebService(BaseWebService):
    """ The BaseBackgroundWebService contains all of the boilerplate code required 
        by WebServices that need to carry out asynchronous requests. For example,
        if you need to run a process concurrently (which may be blocking) then
        you need to inherit from this WebService.
    """
    
    class BaseBackgroundProcess(multiprocessing.Process):
        """ The BaseBackgroundProcess contains the logic of the process you need to
            have running alongside your WebService. This contains the boilerplate
            code needed for the smooth running of your process alongside the 
            web service. You should derive a subclass, overloading only the methods
            allowed (explicitly stated in the comments).
        """
        def __init__(self, receive_queue, send_queue):
            super().__init__()
            
            self.exit_flag        = multiprocessing.Event()
            
            self.__receive_queue  = receive_queue
            self.__send_queue     = send_queue
            self.__worker_process = threading.Thread(target=self.main_loop)
    
        def run(self):
            """ Handles the stopping of the background process cleanly - you should 
                not overload this method. This specifically handles the communication
                between the main process and the background process (passing of
                data etc.)
            """
            logging.debug('BaseBackgroundProcess Starting')
            
            
            self.__worker_process.start()
            
            while not self.exit_flag.is_set():
                self.wait_for_request()
                    
            
            self.__worker_process.join(2)
            
            logging.debug('BaseBackgroundProcess Exiting')
            
        def main_loop(self):
            """ Handles the stopping of the background process cleanly - you should 
                not overload this method. This specifically handles the actual
                work of background process.
            """
            logging.debug('WorkerProcess Starting')
            while not self.exit_flag.is_set():
                self.loop()
            logging.debug('WorkerProcess Exiting')
                
        def loop(self):
            """ This method is called over and over so overload this method 
                with the actual work you need to carry out alongside the WebService.
                It is fine if the work you need to carry out blocks (so it doesn't
                exit from this method) but this may cause it to be terminated 
                with no notice on exit. 
            """
            pass
            
        def wait_for_request(self):
            """ Handles the communication between the background process and the
                WebService. You should not overload this method. 
            """
            try:  
                (received_trans_id, message_received) = self.__receive_queue.get(block=True, timeout=2)
                message_to_send = self.handle_request(message_received)
                self.__send_queue.put( (received_trans_id, message_to_send) )
                self.__receive_queue.task_done()
                self.__send_queue.join()
            except queue.Empty:
                pass
            
        def handle_request(self, message_received):
            """ Overload this method to find out when the WebService wishes 
                to interact with this background process. It does this by passing
                a 'message' which you define and handle. For example, it could be
                that the client has asked for information that only the background
                process can provide. You can also use this to perform operations
                on the background process.  
            """
            return None
        
        def stop(self):
            """ Overload this method to be notified when the background process
                should end.
            """
            pass
            
            
        def shutdown(self):
            """ Attempts to stop the background process. If it takes too long
                or it is blocking and therefore will never exit, the process is
                terminated. You should not overload this method (overload stop
                instead).
            """
            self.exit_flag.set()
            self.stop()
            sleep(2)
            if self.__worker_process.is_alive():
                logging.debug('Worker process forced kill')
                self.__worker_process.terminate()
    
    
    
    
    def __init__(self, web_service_config, background_process_class=None):
        super().__init__(web_service_config)
        
        self._send_queue         = multiprocessing.JoinableQueue()
        self._receive_queue      = multiprocessing.JoinableQueue()
        self.__transaction_id    = 0
        
        if not background_process_class:
            background_process_class = self.BackgroundProcess
        
        self._background_process = background_process_class(self._send_queue, self._receive_queue)
        
    def get_new_transaction_id(self):
        """ Increments the transaction ID and passes it back. This is used
            internally to make sure the response from the background process 
            matches up with the right request. You should not override this
            method.
        """
        self.__transaction_id += 1
        return self.__transaction_id
    
    def request(self, message_to_send, timeout=2):
        """ Makes a request to the background process with a message you provide.
            This subsequently calls handle_request on the background process with
            the mesaage passed in. You can use this to return the requested info
            asked by a client from your background process or to carry out an
            operation on the background process (you define).  
        """
        send_trans_id = self.get_new_transaction_id()
        self._send_queue.put( (send_trans_id, message_to_send) )
        self._send_queue.join()
        
        try:
            while True:
                (received_trans_id, message_received) = self._receive_queue.get(block=True, 
                                                                               timeout=timeout)
                self._receive_queue.task_done()
                
                if send_trans_id == received_trans_id:
                    return message_received
                else:
                    continue
                    
        except queue.Empty:
            pass
            
        return None
    
    
    def start(self):
        """ Starts the background process.
        """
        logging.info('BaseBackgroundWebService Start')
        
        self._background_process.start()
    
    def stop(self):
        """ Attempts to stop the background process but terminates it if it
            takes too long stopping the worker thread.
        """
        logging.info('BaseBackgroundWebService Stop')
        self._background_process.shutdown()
        self._background_process.join(3)
        if self._background_process.is_alive():
            logging.info('Background process forced killed')
            self._background_process.terminate()

        
        
        