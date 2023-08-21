from selenium import webdriver
from const import URL
import os

def build_path(dir: str = ''):
    path = str(os.path.dirname((os.path.realpath(__file__))))
    path = path + '/' + dir
    return path.replace('\\', '/')

def get_content(command: str, champion: str = '', base_url: str = URL):
    def build_url():
        direction = {
            'home': 'champions',
            'champion': 'champion/%s',
            'story': 'story/champion/%s'
        }
        if command not in direction:
            commands = list(direction.keys())
            print('Select from the folllowing commands: %s' % str(commands)[1:-1])
            return None
        rephrased_url = base_url + direction[command]
        return rephrased_url % champion.lower() if '%s' in rephrased_url else rephrased_url

    def fetch(url: str):
        opts = webdriver.ChromeOptions()
        opts.add_argument('--headless')
        driver = webdriver.Chrome(options=opts)
        driver.get(url)
        content = driver.page_source
        driver.close()
        return content

    url = build_url()
    if url is None:
        return None
    return fetch(url)


