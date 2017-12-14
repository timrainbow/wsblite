
# WSBLite - Lightweight Web Service Builder

Want to quickly provide a web interface for your projects? Can't be bothered with all that boilerplate code handling the HTTP requests but you also don't have the time nor want the hassle of adding a dependency on bulky frameworks like Flask or Django? If so then WSBLite is for you!

WSBLite allows you to rapidly build a web service by defining the HTTP methods your web service accepts alongside the url paths your service wishes to be notified about. Want different url paths to be forwarded to different services? No problem. Need your web service to inform a background process, even if it is a blocking process? Easy!

## Requires
 - Python3.5 or later

## Quickstart
Want to quickly see what all the fuss is about? Simply follow the instructions below to see if WSBlite will work for your projects.

Download the code: 
```bash
$ git clone https://github.com/timrainbow/wsblite.git
```

Run the WSBlite script:
```bash
$ cd wsblite/
$ python3 run_wsblite.py --port 9090
```

View the <a href="http://127.0.0.1:9090/" target="_blank">WSBlite homepage</a> once it has started.

You will see a list of web services that were automatically imported from the `webservices` directory - each script relates to a heading on the homepage (note that `root_webservice.py` doesn't show up on the page otherwise it would link you to the same page). Try following the web service links and take a look at the corresponding scripts within the `webservices` directory. 

Feel free to modify the existing examples and rerun WSBlite again to see roughly how they work together to provide a single entry point to different web services.

## Building A Standalone Web Service
Python scripts placed within the `webservices` directory are automatically imported by WSBlite if they contain a class with a name that ends in `WebService` for example: `class MyAwesomeWebService(BaseWebService):`. 

You can see there are already three scripts within the `webservices` directory that will be imported when WSBlite is ran: `list_dir_example.py`, `random_num_example.py` and `root_webservice.py`. If you want to build a standalone web service (i.e. you don't have an existing project you are looking to provide a web interface for), you must place your script within this directory and ensure it contains a class with a name that ends with `WebService` (but the actual script name doesn't matter so long as it ends in `.py`). Or to begin with you can just simply modify one of the existing examples to suit your needs.

Your web service must also inherit from the appropriate WSBlite base class. Which base class your web service inherits from depends on how your web service operates. The base classes are located within the `webcommon` directory.  
## Providing A Web Interface For An Existing Project
Follow these instructions if instead you have an existing project that you now want to provide a web interface for. These instructions will allow you to segregate your project and custom web service code away from the internal workings of WSBlite and leave you free to only worry about the parts that are unique to your web service.

Change directory into your existing project, add WSBlite as a git submodule and initialise it:
```bash
$ cd existing-project/
$ git submodule add https://github.com/timrainbow/wsblite.git
Cloning into '/path/to/existing-project/wsblite'...
remote: Counting objects: 51, done.
remote: Compressing objects: 100% (23/23), done.
remote: Total 51 (delta 13), reused 21 (delta 7), pack-reused 21
Unpacking objects: 100% (51/51), done.
$ git submodule init
```
Move the `webservices` directory contained within the newly downloaded `wsblite` directory into your project:
```bash
$ mv wsblite/webservices ./
```
If you intend for WSBlite to be the entry point for your application (i.e. the user runs WSBlite from the command line which in turn starts up your application) then all you need to do is execute the run script and provide the import directory (where your custom web service will be located):  
```bash
$ python3 wsblite/run_wsblite.py --import_dir=webservices/
```
If instead your application is the entry point which in turn runs WSBlite then add a new Python3 script (or modify one of your existing scripts) to call the `main` function within `run_wsblite.py`. An example script which could be ran by the system at startup is given below:

```python
#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'wsblite'))
from wsblite import run_wsblite
from time import sleep

PORT = 9090

if __name__ == "__main__":
    # GracefulInterruptHandler just allows us to capture the kill command
    # so we can shutdown cleanly.
    with run_wsblite.GracefulInterruptHandler() as signal_handler:
        # We can also supply the import directory containing our web service
        # to the main function if needed. Otherwise it will assume 'webservices'
        # in the directory above wsblite/
        wsblite_controller = run_wsblite.main(port=PORT)
        try:
            while wsblite_controller.is_server_running():
                sleep(1)
                if signal_handler.interrupted:
                    print('Received kill command, attempting graceful shutdown...')
                    break
        except KeyboardInterrupt:
            # This script is designed to be ran by the system (e.g. at startup)
            # but KeyboardInterrupt captured for ease of use.
            print('Received keyboard interrupt...')
        finally:
            wsblite_controller.stop()
```

## Writing Your WebService Class
Before you start writing your new WebService class, you need to decide which WSBlite base class it will inherit from. There are two to choose from depending on how your web service will work:

### Synchronous requests
`base_webservice.py` contains a class called `BaseWebService` which your web service should inherit from if you can perform the operation your web service provides at the time your client requests it. For example, listing the current working directory and returning that to the client - take a look at `list_dir_example.py` to see an example of this.

### Asynchronous requests
`background_webservice.py` contains a class called `BaseBackgroundWebService` which your web service should instead inherit from if either of these statements are true:

 - Your web service needs to constantly operate in the background, even when the client hasn't requested it yet.
 - You need to launch a concurrent process alongside your web service (which might be blocking) and interact with it when the client requests your web service.

The `BaseBackgroundWebService` contains an internal class called `BaseBackgroundProcess` which will hold the code you want to perform concurrently. Like with the `BaseBackgroundWebService`, you will need to construct your own background process class, ensuring that it inherits from `BaseBackgroundProcess` and pass it to the `__init__` method within `BaseBackgroundWebService`. Intricacies such as communication between your web service and background process is provided by inheriting from these classes, leaving you free to just worry about your specific logic rather than handling the complexities of inter-process communication.

To see how this works in action, take a look at `random_num_example.py`.


## Web Service Config
You can register which url paths notify your web service (as well as providing other setup information) by defining your web service configuration. Each derived web service subclass must pass its configuration to the chosen web service base class to be loaded. The examples such as `list_dir_example.py` and  `random_num_example.py` currently do this by simply holding the configuration at the top of their own files in a variable called `WEB_SERVICE_CONFIG`. There is no reason why this could not instead be read in from a file and then passed to the base class.

The web service format looks like this (note that some entries are optional):
```python
{
BaseWebService.CONF_ITM_NAME: '<name of your web service>', 
BaseWebService.CONF_ITM_ENABLED: '<true/false>',
BaseWebService.CONF_ITM_AUTH_ALL_ENABLED: '<true/false>',
BaseWebService.CONF_ITM_OWNED_URLS: 
    {'<url path web service is interested in>': 
        {BaseWebService.CONF_ITM_ALLOW_METH : <list of allowed HTTP Methods>,
         BaseWebService.CONF_ITM_AUTH_BASIC_ENABLED: '<true/false>',
         BaseWebService.CONF_ITM_AUTH_USERNAME: '<username needed for this path>',
         BaseWebService.CONF_ITM_AUTH_PASSWORD: '<password needed for this path>'}
    }
}
```
E.g.
```python
{
BaseWebService.CONF_ITM_NAME: 'My Awesome Web Service', 
BaseWebService.CONF_ITM_ENABLED: 'true',
BaseWebService.CONF_ITM_OWNED_URLS: 
    {'/my_awesome_web_service': 
        {BaseWebService.CONF_ITM_ALLOW_METH : ['GET', 'POST', 'DELETE']}
    }
}
```
or the same config but using authentication...
```python
{
BaseWebService.CONF_ITM_NAME: 'My Awesome Web Service', 
BaseWebService.CONF_ITM_ENABLED: 'true',
BaseWebService.CONF_ITM_AUTH_ALL_ENABLED: 'true',
BaseWebService.CONF_ITM_OWNED_URLS: 
    {'/my_awesome_web_service': 
        {BaseWebService.CONF_ITM_ALLOW_METH : ['GET', 'POST', 'DELETE'],
         BaseWebService.CONF_ITM_AUTH_BASIC_ENABLED: 'true',
         BaseWebService.CONF_ITM_AUTH_USERNAME: 'admin',
         BaseWebService.CONF_ITM_AUTH_PASSWORD: 'MySecretPassword'}
    }
}

```
### Configuration Options

#### General Config

**BaseWebService.CONF_ITM_NAME**
The nicely-formatted name of your web service to show in links etc.

**BaseWebService.CONF_ITM_ENABLED**
You can prevent your web service from being loaded/started by setting this to `false` rather than having to remove your script from the `webservices` directory.

**BaseWebService.CONF_ITM_OWNED_URLS**
A dictionary containing the url paths to register (as the keys in the dictionary) and the allowed HTTP methods as values. It's possible for multiple web services to register their interest in the same url path **if** the allowed HTTP methods do **not** overlap.

**BaseWebService.CONF_ITM_ALLOW_METH**
A list of allowed HTTP methods for a particular url path. The list can contain any combination of `GET`, `PUT`, `POST` and `DELETE`. It's possible for multiple web services to register their interest in the same url path **if** the allowed HTTP methods do **not** overlap.

#### Basic Authentication Config

**BaseWebService.CONF_ITM_AUTH_ALL_ENABLED**
This setting allows you to globally enable or disable authentication for all owned urls by this web service. If set to `true` (the default) then the authentication setting for each owned url is used instead (see `BaseWebService.CONF_ITM_AUTH_BASIC_ENABLED`). Otherwise if set to `false` then the setting for each individually owned url is ignored and authentication is subsequently disabled for your web service throughout. This can be useful for testing purposes.

**BaseWebService.CONF_ITM_AUTH_BASIC_ENABLED**
Each owned url by this web service can have basic authentication enabled by setting this to `true` (defaults to `false` which means no authentication is used). If set to `true` then you must also set a username and password for the client to use (see `BaseWebService.CONF_ITM_AUTH_USERNAME` and `BaseWebService.CONF_ITM_AUTH_PASSWORD`).

**BaseWebService.CONF_ITM_AUTH_USERNAME**
This is the username which must be used to access the associated owned url. You only need to provide this if `BaseWebService.CONF_ITM_AUTH_BASIC_ENABLED` is set to `true` for the owned url.

**BaseWebService.CONF_ITM_AUTH_PASSWORD**
This is the password which must be used to access the associated owned url. You only need to provide this if `BaseWebService.CONF_ITM_AUTH_BASIC_ENABLED` is set to `true` for the owned url.
