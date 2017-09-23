#!/usr/bin/env python3

import argparse
import os
import importlib

import webservice_engine
import logging.config

IMPORT_PACKAGE_NAME = 'webservices'
COMMON_PACKAGE_NAME = IMPORT_PACKAGE_NAME + os.sep + 'common'


def add_parser_arguments(arg_parser):
    arg_parser.add_argument('--port', '-p', type=int, default=9090)
    
    return arg_parser

def parse_command_line():
    arg_parser = argparse.ArgumentParser(description='WebService')
    arg_parser = add_parser_arguments(arg_parser)
    
    return (arg_parser.parse_args(), arg_parser.error)

def expand_arguments(args, error_function):
    expanded_args = {}
             
    # Get args   
    expanded_args['port']  = args.port

    return expanded_args

def import_web_services(import_from):
    """ Searches a given directory for WebService classes and imports them
        (but does not instantiate them). Note that the class names must end with
        'WebService'.
    """
    imported_web_services = list()
    web_services_to_import = os.listdir(import_from)

    for web_service in web_services_to_import:
        logging.debug('Trying ' + str(web_service))
        if len(web_service) < 4 or web_service == '__init__.py' or not web_service.endswith('.py'):
            logging.debug('Skipping ' + str(web_service))
            continue
        # Remove the .py extension
        web_service = web_service[:-3]
        to_import = import_from.replace(os.sep, '.') + "." + web_service
        mod = importlib.import_module(to_import)
        module_attributes = dir(mod)
        for attr in module_attributes:
            if not attr.endswith('WebService'):
                continue
            new_web_service = getattr(mod, attr)
            logging.debug('Adding ' + str(new_web_service))
            imported_web_services.append(new_web_service)
            
    return imported_web_services
        
def main(port):
    """ The main entry into running the web services. The command line hooks into
        this but other scripts can call this directly.
    """
    logging.config.fileConfig('logging.conf')
    logging.info('Starting')
    
    all_web_services = import_web_services(import_from=IMPORT_PACKAGE_NAME)
    web_services_not_to_import = import_web_services(import_from=COMMON_PACKAGE_NAME)
    web_services_to_import = list(set(all_web_services) - set(web_services_not_to_import))
      
    controller = webservice_engine.WebServiceController(port, web_services_to_import)
    try:
        controller.start()
        # TODO: The 'wait for user to interrupt' logic should be moved to the command_line_run
        input('\nPress ENTER to exit...\n\n')
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        controller.stop()

def command_line_run():
    """ Parses the command line before passing the arguments to the main function.
    """
    args, error_function = parse_command_line()
    main(**expand_arguments(args, error_function))
    logging.info('Exiting...')
    
if __name__ == '__main__':
    """ Hook to command line run.
    """
    command_line_run()
