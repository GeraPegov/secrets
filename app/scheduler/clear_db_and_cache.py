scheduler = BackgroundScheduler()



def shemas_cash():
    """
    Инициализация очистки устаревших данных в таблице и очистка кэша. 
    Очистка производится каждый час в соответствии с планировщиком clear_cash()
    """
    logger.info(f'Start shemas_cash')
    try:
        with start_table() as conn:
            with conn.cursor() as curs:
                logger.info(f'Open db in shemas_cash()')
                curs.execute('DELETE FROM secrets_users WHERE last_add < NOW() RETURNING id')
                quanity_id = curs.fetchall() 
                conn.commit()
                if quanity_id:
                    logger.info(f'Delete {len(quanity_id)} id(cache)')
                    for i in quanity_id:
                        if i in cache:
                            del cache[i]        
    except Exception as e:
        raise HTTPException(status_code=404)

def clear_cash():
    logger.info(f'Start clear_cash')
    scheduler.add_job(shemas_cash, 'interval', minutes=60)
    scheduler.start()
    logger.info(f'End clear_cash')

def startup():
    init_db()
    logger.info('Start lifespan')
    clear_cash()