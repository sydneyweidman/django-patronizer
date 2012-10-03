import os
import uno
import logging
import subprocess
from multiprocessing import Process
from time import sleep
from com.sun.star.connection import ConnectionSetupException
from com.sun.star.connection import NoConnectException
from com.sun.star.lang import DisposedException

log = logging.getLogger(__name__)
logging.basicConfig()
log.setLevel(logging.DEBUG)

env = dict(PYTHONPATH=os.getenv('PYTHONPATH'), PATH=os.getenv('PATH'))

class Options(object):

    def __init__(self, options, prefix='-'):
        for opt in options:
            setattr(self, opt, True)
        self._options = options
        self.prefix = prefix

    def __str__(self):
        return ' '.join([self.prefix + i for i in self._options])

    def __repr__(self):
        return self.__str__()
    
class UnoService(object):

    defaults = {'oobin':     '/usr/bin/soffice',
                'options': ['headless','invisible'],
                'accept':  '"socket,host={host},port={port};urp;StarOffice.ComponentContext"',
                'connectstr': 'uno:socket,host={host},port={port};urp;StarOffice.ServiceManager',
                'host':    'localhost',
                'port':    '2002',
                'env':     env,
                'timeout': 5,
                }

    def __init__(self, oobin=defaults['oobin'], options=defaults['options'],
                 accept=defaults['accept'], connectstr=defaults['connectstr'],
                 host=defaults['host'], port=defaults['port'], env=defaults['env'],
                 timeout=defaults['timeout']):
        """Run OpenOffice/LibreOffice as a service, return desktop
        object for script interaction.

        `bin`: office executable
        `options`: a list of boolean command-line options (other than accept)
        `accept`: The accept string passed to the --accept option. Must contain {host} and {port} format strings.
        `connectstr`: The connect string used by the resolver to connect to the service. Must contain {host} and {port}
        `host`: The connect and accept host. Defaults to localhost
        `port`: The connect and accept port. Defaults to 2002 (string)
        `env`: The environment to pass to the process starting LibreOffice
        `timeout`: Timeout in seconds before retrying start
        """
        self.oobin = oobin
        self.options = Options(options)
        self.host = host
        self.port = port
        self.accept = accept.format(host=self.host, port=self.port)
        self.connectstr = connectstr.format(host=self.host, port=self.port)
        self.env = env
        self.timeout = timeout
        self.desktop = None
        self.proc = None

    def start(self):
        """Start the uno listener so that we can get a context. Return True if the process starts"""
        basecmd = "{oobin} {options} -accept={accept}"
        cmd = basecmd.format(oobin=self.oobin, options=self.options, accept=self.accept)
        log.info('Command: %s' % (cmd,))
        args = (cmd,)
        kwargs = {'env':self.env, 'stdout':subprocess.PIPE, 'stderr':subprocess.STDOUT, 'shell':True }
        self.proc = Process(target=subprocess.Popen, args=args, kwargs=kwargs)
        self.proc.start()
        return self.proc.pid
        
    def _connect(self):
        try:
            localContext = uno.getComponentContext()

            resolver = localContext.ServiceManager.createInstanceWithContext(
                       "com.sun.star.bridge.UnoUrlResolver", localContext)

            smgr = resolver.resolve(self.connectstr)
            remoteContext = smgr.getPropertyValue("DefaultContext")

            self.desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop",remoteContext)
            return self.desktop

        except (NoConnectException, ConnectionSetupException):
            logging.exception("UNO server not started.")
            raise 
        
    def connect(self, try_start=True):
        """Connect to the running LibreOffice process and return a
        com.sun.star.frame.Desktop"""
        self.start()
        sleep(self.timeout)
        if self.proc:
            return self._connect()
        else:
            return None

    def terminate(self):
        """Terminate the Desktop instance"""
        try:
            self.desktop.terminate()
        except DisposedException:
            pass
        finally:
            if self.proc:
                log.warn('Terminating LibreOffice PID %d' % (self.proc.pid,))
                self.proc.terminate()
