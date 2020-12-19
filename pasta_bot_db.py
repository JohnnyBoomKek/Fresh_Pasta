import sqlite3
import os
from dotenv import load_dotenv
# for catching sqlite exceptions
import traceback
import sys
import time
import requests


# load env variables
load_dotenv()
VK_ACCESS_TOKEN = os.getenv('VK_ACCESS_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

DOMAINS = [
    'pastachn',
    'internetpasta']

def ensure_connection(func):

    def inner(*args, **kwargs):
        with sqlite3.connect('pasta_bot.db') as conn:
            res = func(*args, conn=conn, **kwargs)
        return res

    return inner

@ensure_connection
def get_last_post_id(conn):
    c = conn.cursor()
    c.execute('SELECT pk FROM pasta ORDER BY pk DESC LIMIT 1')
    r, = c.fetchone()
    return r

@ensure_connection
def get_last_read(user_id, conn):
    c = conn.cursor()
    c.execute('SELECT last_read FROM user WHERE tg_id = ? LIMIT 1', (user_id,))
    r, = c.fetchone()
    return r

@ensure_connection
def get_username(user_id, conn):
    c = conn.cursor()
    c.execute('SELECT username FROM user WHERE tg_id = ?', (user_id,))
    r, = c.fetchone()
    return r

@ensure_connection
def user_exists(conn,user_id):
    c = conn.cursor()
    c.execute('SELECT EXISTS(SELECT 1 FROM user WHERE tg_id=? LIMIT 1)', (user_id,))
    r, = c.fetchone()
    return r == 1

@ensure_connection
def get_post_text(post_id, conn):
    c = conn.cursor()
    c.execute('SELECT text FROM pasta WHERE pk = ?', (post_id,))
    r, = c.fetchone()
    return r



#update funcs 

@ensure_connection
def update_last_read(user_id, conn):
    c = conn.cursor()
    c.execute('UPDATE user SET last_read = last_read + 1 WHERE tg_id = ?', (user_id,))
    conn.commit()

@ensure_connection
def init_db(conn, force: bool = False):
    c = conn.cursor()

    if force:
        c.execute('DROP TABLE IF EXISTS pasta')
        c.execute('DROP TABLE IF EXISTS user')

    c.execute('''
        CREATE TABLE IF NOT EXISTS pasta(
            pk          INTEGER PRIMARY KEY AUTOINCREMENT,
            vk_id       INTEGER,
            likes       INTEGER,
            text        TEXT,
            domain      VARCHAR(50),
            audio       VARCHAR(50)
        )
    ''')
    conn.commit()

    c.execute('''
        CREATE TABLE IF NOT EXISTS user(
            pk          INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id          INTEGER,
            username    VARCHAR(50),
            last_read   INTEGER
        )
    ''')
    conn.commit()

def get_new_post(domain, offset=0):
    if offset > 10:
        print('Something went wrong')
        return None
    
    req_data = {
        'access_token':VK_ACCESS_TOKEN,
        'domain':domain,
        'count':1,
        'offset':offset,
        'v': '5.92',

    }   
    url = "https://api.vk.com/method/wall.get"
    post_list = requests.post(url, req_data)
    vk_id = post_list.json()['response']['items'][0]['id']
    text = post_list.json()['response']['items'][0]['text']
    likes = post_list.json()['response']['items'][0]['likes']['count']
    is_pinned = 'is_pinned' in post_list.json()['response']['items'][0].keys()
    marked_as_ads = post_list.json()['response']['items'][0]['marked_as_ads'] == 1
    
    if is_pinned or marked_as_ads:
        record = get_new_post(domain, offset+1)
    else:
        record = (vk_id, likes, text.replace("\n",""), domain, None)
    return record

@ensure_connection
def add_pasta(conn, record):
    try:
        c = conn.cursor()
        c.execute(
            ' INSERT INTO pasta (vk_id, likes, text, domain, audio) VALUES(?,?,?,?,?)', record)
        conn.commit()
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))

@ensure_connection
def add_user(conn, user):
    try:
        c = conn.cursor()
        c.execute(
            ' INSERT INTO user (tg_id, username, last_read) VALUES(?,?,?)', user)
        conn.commit()
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))

@ensure_connection
def remove_user(conn, user):
    try:
        c = conn.cursor()
        c.execute(
            ' DELETE FROM user WHERE tg_id=?', user)
        conn.commit()
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))

@ensure_connection
def update_likes(conn, domain, offset=0):
    c = conn.cursor()
    c.execute('SELECT COUNT(pk) FROM pasta WHERE domain=?', (domain,))
    cnt = c.fetchone()[0]
    print(f'update likes: you got {cnt} posts from {domain}' )
    if cnt < 1:
        return
    elif cnt > 100:
        cnt = 100
    
    req_data = {
        'access_token':VK_ACCESS_TOKEN,
        'domain':domain,
        'count':cnt,
        'v': '5.92',
        'offset':offset,

    }   
    url = "https://api.vk.com/method/wall.get"
    post_list = requests.post(url, req_data)
    for i in range(cnt):
        vk_id = post_list.json()['response']['items'][i]['id']
        likes = post_list.json()['response']['items'][i]['likes']['count']
        is_pinned = 'is_pinned' in post_list.json()['response']['items'][0].keys()
        marked_as_ads = post_list.json()['response']['items'][0]['marked_as_ads'] == 1
        print('updating likes: ', vk_id, likes)
        c.execute('UPDATE pasta SET likes = ? WHERE vk_id = ?', (likes, vk_id))
        print('updated', vk_id, likes)
        conn.commit()
    if is_pinned or marked_as_ads:
        update_likes(domain=domain, offset=offset+1)
    else:
        return
            




@ensure_connection
def main(conn):
    while True:
        try:
            c = conn.cursor()
            for domain in DOMAINS:
                c.execute(f'SELECT vk_id FROM pasta WHERE domain = ? ORDER BY pk DESC LIMIT 1', (domain,))
                last_vk_id = c.fetchone()
                new_post = get_new_post(domain)
                if new_post is not None:
                    if last_vk_id is None or new_post[0] != last_vk_id[0]:
                        add_pasta(record=new_post)
                update_likes(domain=domain)
            if(conn):
                c.close()
                print('Connection is closed.')
        except Exception as e:
            print('Something went wrong!')
            print("Error: ", e)
            time.sleep(5)
            continue
        print('Waiting for next request..')
        time.sleep(300)

if __name__=="__main__":
    init_db(force=True)
    main()