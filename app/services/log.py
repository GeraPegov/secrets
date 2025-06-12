import logging


def start_logging():
    format = logging.Formatter(
        '''[%(asctime)s.%(msecs)03d]
        %(module)10s:%(lineno)-3d %(levelname)7s - %(message)s
        '''
    )

    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(format)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler]
    )
