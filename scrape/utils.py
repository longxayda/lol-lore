from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from const import URL, PARALLEL
import concurrent.futures
import os
import typing as T
import json

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
        WebDriverWait(driver, 4)
        content = driver.page_source
        driver.close()
        return content

    url = build_url()
    if url is None:
        return None
    print(url)
    return fetch(url)


def parallelize(iterables: T.Iterable, function: T.Callable, timeout: int = None, concurrency: int = PARALLEL):
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        step = concurrency
        idx = 0
        output = []
        while True:
            iterable = iterables[idx * step : (idx + 1) * step]
            if len(iterable):
                for res in executor.map(function, iterable, timeout=timeout):
                    output.append(res)
                idx += 1
            else:
                break
        return output
    
    
def coalesce(source: T.Dict[str, str], target: T.Dict[str, str]):
    for key in target:
        value = target[key] if (target[key] or key not in source) else source[key]
        target[key] = value
    return target

def validate():
    def helper(data: T.Dict[str, str]):
        def check(value: T.Union[None, str, T.List]):
            return value != '' and value != None and value != []
        res = {key: check(data[key]) for key in data}
        res['race'] = True # ignore Race flag because we don't really know
        return all(res.values())

    base_path = build_path('../out/json/info')

    scrape_dirs = os.listdir(base_path)

    output = {}
    bad_data = []

    precise_path = f'{base_path}/%s/data.json'

    if scrape_dirs:
        for scrape_dir in scrape_dirs:
            with open(precise_path % scrape_dir, 'r', encoding='utf-8') as file:
                data = json.load(file)
                is_valid = helper(data)
                if not is_valid:
                    bad_data.append(data)
                output[scrape_dir] = is_valid
                
        invalid_path = build_path('../out/json/invalid.json')

        with open(invalid_path, 'w', encoding='utf-8') as file:
            json.dump(bad_data, file, indent=2)

    return bad_data

