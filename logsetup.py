LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'loggers': {
        '': {  # root logger
            'level': 'INFO',
            'handlers': ['file_handler'],
            'propagate': False
        }
    },
    'handlers': {
        'file_handler': {
            'level': 'INFO',
            'formatter': 'info',
            'class': 'logging.FileHandler',
            'filename': 'logs/info.log',
            'mode': 'a'
        }
    },
    'formatters': {
        'info': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s::%(module)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%m-%d-%Y@%H:%M:%S'
        }
    }
}