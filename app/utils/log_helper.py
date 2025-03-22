import logging

LEVEL = logging.INFO
FORMAT = logging.Formatter(
    fmt=(
        "%(asctime)s.%(msecs)03d :: "
        "%(levelname)-6s :: "
        "%(name)-30s:%(lineno)-4d --- "
        "%(message)s"
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
)


def log_setup(logger_name):
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    logger.setLevel(LEVEL)

    console_logger = logging.StreamHandler()
    console_logger.setLevel(LEVEL)
    console_logger.setFormatter(FORMAT)

    logger.addHandler(console_logger)
