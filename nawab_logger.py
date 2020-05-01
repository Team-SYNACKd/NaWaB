import logging


class Nawab_Logging(object):

    def __init__(self, dirpath, level):
       self.setup_logger('Results', dirpath + "results.log", level)
       self.setup_logger('Error', dirpath + "error.log", level)

     ##setting up the logger
    def setup_logger(self, logger_name, log_file, level=logging.INFO):
        log_setup = logging.getLogger(logger_name)
        formatter = logging.Formatter(
            '%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        fileHandler = logging.FileHandler(log_file, mode='a')
        fileHandler.setFormatter(formatter)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        ## Clear up any existing in handler
        log_setup.setLevel(level)
        if (log_setup.hasHandlers()):
            log_setup.handlers.clear()
        log_setup.addHandler(fileHandler)
        log_setup.addHandler(streamHandler)
        log_setup.propagate = False

    def logger(self, msg, level, logfile):

        if logfile == 'Results':
            log = logging.getLogger('Results')
        elif logfile == 'Error':
            log = logging.getLogger('Error')
        else:
            print('Invalid logging option')

        if level == 'info':
            log.info(msg)
        elif level == 'warning':
            log.warning(msg)
        elif level == 'error':
            log.error(msg)
        else:
            print('Invalid message')
