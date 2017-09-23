# WSBLite - Lightweight Web Service Builder

Want to quickly provide a web interface for your projects? Can't be bothered with all that boilerplate code handling the HTTP requests but you also don't have the time nor want the hassle depending on bulky frameworks like Flask or Django? If so then WSBLite is for you!

WSBLite allows you to rapidly build a web service by defining the HTTP methods  your web service accepts alongside the url paths your service wishes to be notified about. Want different url paths to be forwarded to different services? No problem. Need your web service to inform a background process, even if it is a blocking process? Easy!

## Requires
 - Python3.5 or later

## Quickstart
Download the code: 
```bash
git clone https://github.com/timrainbow/wsblite.git
```

Run the WSBlite script:
```bash
cd wsblite/
python3 run_wsblite.py --port 9090
```

View the <a href="http://127.0.0.1:9090/" target="_blank">WSBlite homepage</a> once it has started.

You will see a list of web services that were automatically imported from the `webservices` directory - each script relates to a link on the homepage. Try following the web service links and take a look at the corresponding scripts within the `webservices` directory. 

Feel free to modify the existing examples and rerun WSBlite again to see roughly how they work together to provide a single entry point to different web services.

## Building your own web service
Python scripts placed within the `webservices` directory are automatically imported by WSBlite if they contain a class with a name that ends in `WebService` for example: `class MyAwesomeWebService(BaseWebService):`. 

You can see there are already three scripts within the `webservices` directory that will be imported when WSBlite is ran: `list_dir_example.py`, `random_num_example.py` and `root_webservice.py`. When you build your web service, you must place your script within this same directory and ensure it contains a class with a name that ends with `WebService`. Or to begin with you can just simply modify one of the existing examples to suit your needs.

Your web service must also inherit from the appropriate base class (depending on how your web service operates). The base classes are located within the `common` directory which is found within the `webservices` directory .  

### Synchronous requests
`base_webservice.py` contains a class called `BaseWebService` which your web service should inherit from if you can perform the operation your web service provides at the time your client requests it. For example, listing the current working directory and returning that to the client - take a look at `list_dir_example.py` to see an example of this.

### Asynchronous requests
`background_webservice.py` contains a class called `BaseBackgroundWebService` which your web service should instead inherit from if either of these statements are true:

 - Your web service needs to constantly perform the same operation in the background, even when the client hasn't requested it yet.
 - You need to launch a concurrent process alongside your web service (which might be blocking) and interact with it when the client requests your web service.

The `BaseBackgroundWebService` contains an internal class called `BaseBackgroundProcess` which will hold the code you want to perform concurrently. Like with the `BaseBackgroundWebService`, you will need to construct your own background process class, ensuring that it inherits from `BaseBackgroundProcess` and pass it to the `__init__` method within `BaseBackgroundWebService`. Intricacies such as communication between your web service and background process is provided by inheriting from these classes, leaving you free to just worry about your specific logic.

To see how this works in action, take a look at  the `random_num_example.py`.

## Web Service Config
You can register which url paths notify your web service (as well as providing other setup information) by defining your web service configuration. Each derived web service subclass must pass its configuration to the chosen web service base class to be loaded. The examples such as `list_dir_example.py` and  `random_num_example.py` currently do this by simply holding the configuration at the top of their own files in a variable called `WEB_SERVICE_CONFIG`. There is no reason why this could not be read in from a file though if desired.

The web service format looks like this:
```bash
{
BaseWebService.CONF_ITM_NAME: '<name of your web service>', 
BaseWebService.CONF_ITM_ENABLED: '<true/false>',
BaseWebService.CONF_ITM_OWNED_URLS: 
    {'<url path web service is interested in>': 
        {BaseWebService.CONF_ITM_ALLOW_METH : <list of allowed HTTP Methods>}
    }
}
```
E.g.
```bash
{
BaseWebService.CONF_ITM_NAME: 'My Awesome Web Service', 
BaseWebService.CONF_ITM_ENABLED: 'true',
BaseWebService.CONF_ITM_OWNED_URLS: 
    {'/my_awesome_web_service': 
        {BaseWebService.CONF_ITM_ALLOW_METH : ['GET', 'POST', 'DELETE']}
    }
}
```
### Configuration Options

**BaseWebService.CONF_ITM_NAME**
The nicely-formatted name of your web service to show in links etc.

**BaseWebService.CONF_ITM_ENABLED**
You can prevent your web service from being loaded/started by setting this to `false` rather than having to remove your script from the `webservices` directory.

**BaseWebService.CONF_ITM_OWNED_URLS**
A dictionary containing the url paths to register (as the keys in the dictionary) and the allowed HTTP methods as values. It's possible for multiple web services to register their interest in the same url path **if** the allowed HTTP methods do **not** overlap.

**BaseWebService.CONF_ITM_ALLOW_METH**
A list of allowed HTTP methods for a particular url path. The list can contain any combination of `GET`, `PUT`, `POST` and `DELETE`. It's possible for multiple web services to register their interest in the same url path **if** the allowed HTTP methods do **not** overlap.
