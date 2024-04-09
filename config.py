import configparser

CONFIG_FILE = 'overlay.conf'

def init_config():
    try:
        conf = configparser.ConfigParser()
        conf['DEFAULT'] = {
            'content': 'content',
            'content_user': 'content_user',
            'content_password': 'content_password',
            'src': 'src',
            'dst': 'dst',
            'overlay': 'overlay',
            'list': 'zip.xlsx',
            'log': 'log.txt',
        }

        with open(CONFIG_FILE, 'w') as f:
            conf.write(f)

        return conf

    except IOError:
        print('Error create config file!')
        

def read_config(file=CONFIG_FILE):
    conf = configparser.ConfigParser()
    try:
        conf.read_file(open(file))
        return conf

    except:
        return init_config()
