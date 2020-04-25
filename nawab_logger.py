import logging


class Nawab_Logging(object):
    
    def __init__(self, dirpath):
       self.setup_logger('log_result', dirpath + "results.log")
       self.setup_logger('log_error', dirpath + "error.log")
        
    
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
        
        pass
    
    def logger(self, msg, level, logfile):

        if logfile == 'results':
            log = logging.getLogger('log_result')
        if logfile == 'error':
            log = logging.getLogger('log_error')
        if level == 'info':
            log.info(msg)
        if level == 'warning':
            log.warning(msg)
        if level == 'error':
            log.error(msg)
        pass
    

        
    