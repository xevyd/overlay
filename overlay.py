#!/usr/bin/python3
import os
import time
import logging
import subprocess
import pandas as pd
from config import read_config

def get_zips(xls_file):
    if os.path.exists(xls_file):
        try:
            xlsx = pd.ExcelFile(xls_file, engine='openpyxl')
            data = xlsx.parse(xlsx.sheet_names[-1], header=None, na_values=['0'],
                              names=['name', 'age', 'smoke', 'social'])
            data['age'] = data['age'].str.replace(' ', '')

            return data.to_dict(orient='records')

        except Exception as ex:
            logging.error(ex)
            return ''

    else:
        return ''

def overlay_file(item):
    name = ''
    if item['age'] != '':
        name += item['age']
    if str(item['smoke']) != 'nan':
        name += 'smoke'
    if str(item['social']) != 'nan':
        name += '_sn'

    return name + '.mov'

def get_duration(filename):
    cmd = ['ffprobe', '-i', filename]
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    return str([x for x in result.stdout.readlines() if "Duration" in str(x)][-1].strip()).split(' ')[1].split(',')[0]

def get_resolution(file_name):
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of',
           'csv=s=x:p=0', '-i', file_name.encode('utf-8')]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)

    return str(result.stdout).split("'")[1].replace('\\n', '').split('x')

def overlay(params):
    resolution = get_resolution(params['src'])
    cmd = '/usr/bin/ffmpeg -y -hwaccel cuda -i "{}" -vcodec h264_nvenc -c:s copy -vf "movie={}'\
          .format(params['src'], params['overlay'])

    if ['1280', '720'] == resolution:
        cmd += ',setpts=PTS-STARTPTS+5/TB [inner]; [in][inner] overlay [out]" -b:v 8M -b:a 400k '

    elif ['720', '576'] == resolution:
        cmd += ',scale=720:576,setpts=PTS-STARTPTS+5/TB [inner]; [in][inner] overlay [out]" -b:v 8M -b:a 400k '

    elif ['1920', '1080'] == resolution:
        cmd += ',setpts=PTS-STARTPTS+5/TB [inner]; [0:v]scale=1280:720[in]; [in][inner] overlay [out]" -b:v 8M -b:a 400k '

    cmd += '"' + params['dst'] + '"'
    proc = subprocess.call(cmd, shell=True)


def mount_content():
    if not os.path.exists(config['dst']):
        os.makedirs(config['dst'])
    os.system("mount -t cifs -o username={},password={},iocharset=utf8 {} {}".format(
        config['content_user'], config['content_password'], config['content'], config['src']))

config = read_config('/srv/overlay/overlay.conf').defaults()
start_time = time.time()
logging.basicConfig(filename=config['log'], level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logging.info("start encoding {0}".format(start_time))
zips_list = get_zips(config['list'])

if zips_list != '':
    mount_content()
    for item in zips_list:
        filename, fileext = os.path.splitext(item['name'])
        params = {
            'src': os.path.join(config['src'], item['name']),
            'dst': os.path.join(config['dst'], filename + ' ' + item['age'] + fileext),
            'overlay': os.path.join(config['overlay'], overlay_file(item)),
        }

        if not os.path.exists(params['overlay']):
            logging.error('No such file: ' + params['overlay'])
            continue

        if os.path.exists(params['src']) and not os.path.exists(params['dst']):
            item_encode_start_time = time.time()
            overlay(params)
            logging.info(item['name'] + ' ' + get_duration(params['src']) + ' ЗИП: ' + overlay_file(item) +
                         ' encoded in {0}'.format(time.time() - item_encode_start_time) + ' seconds')

else:
    logging.info('empty list')

logging.info("finally {0}\n".format(time.time() - start_time))
