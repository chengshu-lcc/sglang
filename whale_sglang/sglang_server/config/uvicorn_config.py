UVICORN_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
        },
        "access": {
            "formatter": "access",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/uvicorn_access.log",
            "maxBytes": 256 * 1024,
            "backupCount": 4,
        }
    },
    "loggers": {
        "uvicorn.access": {"handlers": ["access"], "level": "DEBUG", "propagate": False},
        "uvicorn.protocols.websockets": {"handlers": ["default"], "level": "DEBUG"},
        "websockets": {"handlers": ["default"], "level": "DEBUG"},
    },
}
