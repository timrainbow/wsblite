#!/usr/bin/env python3

import argparse
import os
import importlib
import signal
import webservice_engine
import logging.config

from time import sleep

IMPORT_PACKAGE_NAME = 'webservices/'
COMMON_PACKAGE_NAME = 'webcommon/'
LOG_CONF_NAME       = 'logging.conf'

class GracefulInterruptHandler(object):
    def __init__(self, sig=signal.SIGTERM):
        self.sig = sig

    def __enter__(self):

        self.interrupted = False
        self.released = False

        self.original_handler = signal.getsignal(self.sig)

        def handler(signum, frame):
            self.release()
            self.interrupted = True

        signal.signal(self.sig, handler)

        return self

    def __exit__(self, type, value, tb):
        self.release()

    def release(self):

        if self.released:
            return False

        signal.signal(self.sig, self.original_handler)

        self.released = True

        return True


def add_parser_arguments(arg_parser):
    arg_parser.add_argument('--port', '-p', type=int, default=9090)
    arg_parser.add_argument('--import_dir', '-i', type=str)
    arg_parser.add_argument('--common_dir', '-c', type=str)
    arg_parser.add_argument('--log_config', '-l', type=str)
    arg_parser.add_argument('--system_run', '-s', action="store_true")

    return arg_parser

def parse_command_line():
    arg_parser = argparse.ArgumentParser(description='WebService')
    arg_parser = add_parser_arguments(arg_parser)
    
    return (arg_parser.parse_args(), arg_parser.error)

def expand_arguments(args, error_function):
    expanded_args = {}
    
    script_dir = os.path.dirname(__file__)
    
    if args.import_dir:
        expanded_args['import_dir'] = os.path.abspath(args.import_dir)
    else:
        expanded_args['import_dir'] = os.path.abspath(os.path.join(script_dir, IMPORT_PACKAGE_NAME))
        
    if args.common_dir:
        expanded_args['common_dir'] = os.path.abspath(args.common_dir)
    else:
        expanded_args['common_dir'] = os.path.abspath(os.path.join(script_dir, COMMON_PACKAGE_NAME))
        
    if args.log_config:
        expanded_args['log_config'] = os.path.abspath(args.log_config)
    else:
        expanded_args['log_config'] = os.path.abspath(os.path.join(script_dir, LOG_CONF_NAME))
              
    expanded_args['port']       = args.port
    expanded_args['system_run'] = args.system_run

    return expanded_args

def import_web_services(import_from):
    """ Searches a given directory for WebService classes and imports them
        (but does not instantiate them). Note that the class names must end with
        'WebService'.
    """
    imported_web_services = list()
    
    if not import_from:
        logging.error('Cannot import from directory as path given is empty')
        return imported_web_services
    elif import_from[-1:] != os.sep:
        # Path needs to have a slash on the end which is sometimes missing
        import_from += os.sep
    
    web_services_to_import = os.listdir(import_from)
    
    # import the containing package first
    import_package = os.path.basename(os.path.dirname(import_from))
    importlib.import_module(import_package)

    for web_service in web_services_to_import:
        logging.debug('Trying ' + str(web_service))
        if len(web_service) < 4 or web_service == '__init__.py' or not web_service.endswith('.py'):
            logging.debug('Skipping ' + str(web_service))
            continue
        # Remove the .py extension
        web_service = web_service[:-3]
        to_import = '.' + web_service
        
        logging.debug('Importing: ' + to_import + ' From Package: ' + import_package)
        mod = importlib.import_module(to_import, import_package)
        module_attributes = dir(mod)
        for attr in module_attributes:
            if not attr.endswith('WebService'):
                continue
            new_web_service = getattr(mod, attr)
            logging.debug('Adding ' + str(new_web_service))
            imported_web_services.append(new_web_service)
            
    return imported_web_services
        
def main(port, import_dir, common_dir, log_config, system_run):
    """ The main entry into running the web services. The command line hooks into
        this but other scripts can call this directly.
    """
    if log_config:
        logging.config.fileConfig(log_config)
    if not import_dir:
        # import webservices from the directory above
        import_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                  IMPORT_PACKAGE_NAME)
        if import_dir[-1:] != os.sep:
            import_dir += os.sep
    if not common_dir:
        common_dir = os.path.join(os.path.dirname(__file__), COMMON_PACKAGE_NAME)
        
        
    logging.info('Starting')
    
    logging.debug('Import Directory: ' + import_dir)
    logging.debug('Common Directory: ' + common_dir)
    logging.debug('Log Config: ' + log_config)
    logging.debug('Port: ' + str(port) )
    
    all_web_services = import_web_services(import_from=import_dir)
    web_services_not_to_import = import_web_services(import_from=common_dir)
    web_services_to_import = list(set(all_web_services) - set(web_services_not_to_import))
      
    controller = webservice_engine.WebServiceController(port, web_services_to_import)
    controller.start()
    
    return controller

def command_line_run():
    """ Parses the command line before passing the arguments to the main function.
    """
    args, error_function = parse_command_line()
    
    try:
        controller = main(**expand_arguments(args, error_function))
        if args.system_run:
            logging.info('Running...')
            with GracefulInterruptHandler() as signal_handler:
                while controller.is_server_running():
                    sleep(1)
                    if signal_handler.interrupted:
                        logging.info('Received kill command, attempting graceful shutdown')
                        break
        else:
            input('\nPress ENTER to exit...\n\n')
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        controller.stop()
        
    logging.info('Exiting...')
    
if __name__ == '__main__':
    """ Hook to command line run.
    """
    command_line_run()
