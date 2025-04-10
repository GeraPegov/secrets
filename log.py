import logging

def start_logging():
    format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(format)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers = [file_handler]
    )