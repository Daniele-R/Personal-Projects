#Some of these are forcefully implemented for debugging

import win32timezone                    # Ensures proper handling of timezones for logs
import pythoncom                        # Required to initialize COM libraries in multi-threaded service
import pywintypes                       # Windows-specific Python error types
import win32service                     # Base service class
import servicemanager                   # Logs messages to the Windows Event Viewer
import win32serviceutil                 # Utilities for installing and handling services
import win32event                       # Allows handling of Windows event objects
import os                               # Used for file paths and process operations
import traceback                        # For detailed exception stack traces
import logging                          # Built-in logging module

from restart import launch_main, CHECK_INTERVAL, EXE_PATH, is_process_running   # Core logic imports

# Set up logging to a local file named 'watchdog_service.log'
LOG_FILE = os.path.join(os.path.dirname(__file__), "watchdog_service.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

# Service configuration
SERVICE_NAME         = "WatchdogService"                                        # Internal service name
SERVICE_DISPLAY_NAME = "Python USB-Detector Watchdog"                           # Displayed in the Windows Services manager

# Define the service class by inheriting from the base framework
class WatchdogSvc(win32serviceutil.ServiceFramework):
    _svc_name_        = SERVICE_NAME
    _svc_display_name_= SERVICE_DISPLAY_NAME

    def __init__(self, args):
        super().__init__(args)                                                  # Initialize base class
        logging.debug("Service __init__")
        self.hWaitStop    = win32event.CreateEvent(None, 0, 0, None)            # Event to handle stop requests
        self.stop_requested = False                                             # Flag for service termination

    def SvcStop(self):
        logging.debug("SvcStop called")
        self.stop_requested = True
        win32event.SetEvent(self.hWaitStop)                                     # Trigger event to stop main loop

    def SvcDoRun(self):
        logging.debug("SvcDoRun start")
        try:
            # Notify Windows Service Manager that service is starting
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, "")
            )

            self.ReportServiceStatus(win32service.SERVICE_RUNNING)              # Mark status as RUNNING
            logging.debug("Reported SERVICE_RUNNING to SCM")

            launch_main()                                                       # Launch the main executable once
            logging.debug(f"Launched main exe: {EXE_PATH}")

            # Begin the watchdog loop to monitor the process
            exe_name = os.path.basename(EXE_PATH)
            while not self.stop_requested:
                running = is_process_running(exe_name)                          # Check if the EXE is still active
                logging.debug(f"Checked {exe_name} running: {running}")
                if not running:
                    launch_main()                                               # Relaunch if not running
                    logging.debug(f"Restarted main exe: {EXE_PATH}")

                rc = win32event.WaitForSingleObject(                            # Wait for stop event or timeout
                    self.hWaitStop,
                    int(CHECK_INTERVAL * 1000)
                )
                if rc == win32event.WAIT_OBJECT_0:
                    break                                                       # Exit if stop requested

            # Notify Windows Service Manager that service stopped
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, "")
            )
            logging.debug("SvcDoRun exiting cleanly")

        except Exception:
            err = traceback.format_exc()                                        # Capture detailed stack trace
            servicemanager.LogErrorMsg(f"Unhandled exception in service:\n{err}")
            logging.error(f"Unhandled exception in service:\n{err}")
            raise                                                               # Reraise so the Service Control Manager knows it failed

# Main execution point for running the service interactively
if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(WatchdogSvc)                             # Allow command-line management of the service
