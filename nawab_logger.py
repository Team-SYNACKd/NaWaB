import logging


class Nawab_Logging(object):

    def __init__(self, dirpath):
       self.setup_logger('result', dirpath + "results.log")
       self.setup_logger('error', dirpath + "error.log")

     ##setting up the logger
    def setup_logger(self, logger_name, log_file, level=logging.INFO):
        log_setup = logging.getLogger(logger_name)
        formatter = logging.Formatter(
            '%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        fileHandler = logging.FileHandler(log_file, mode='a')
        fileHandler.setFormatter(formatter)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        log_setup.setLevel(level)
        log_setup.addHandler(fileHandler)
        log_setup.addHandler(streamHandler)

    def logger(self, msg, level, logfile):

        if logfile == 'results':
            log = logging.getLogger('result')
        elif logfile == 'error':
            log = logging.getLogger('error')
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
