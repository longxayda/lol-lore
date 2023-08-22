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
        res = {}
        for key in data:
            if key == 'race':
                res['race'] = True
                if data['race'] == '':
                    res['race'] = False
            elif key == 'biography':
                res['biography'] = True
                if data[key] == []:
                    res['biography'] = False
                else:
                    for ele in data[key]:
                        if ele == '':
                            res['biography'] = False
                            break
            else:
                res[key] = data[key] != '' and data[key] is not None

        output = all(res.values())
        
        return output

    ref_path = build_path('../out/json/champs.json')

    ref_data = []

    with open(ref_path, 'r', encoding='utf-8') as file:
        ref_data = [data['ref_name'] for data in json.load(file)]

    base_path = build_path('../out/json/info')

    scrape_dirs = os.listdir(base_path)

    output = {}
    bad_data = [champ_name for champ_name in ref_data if champ_name not in scrape_dirs]

    precise_path = f'{base_path}/%s/data.json'
    invalid_path = build_path('../out/json/invalid.json')

    if scrape_dirs and ref_data:
        for scrape_dir in scrape_dirs:
            if os.path.isfile(precise_path % scrape_dir):
                with open(precise_path % scrape_dir, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    is_valid = helper(data)
                    if not is_valid:
                        bad_data.append(data['ref_name'])
                    output[scrape_dir] = is_valid
            else:
                output[scrape_dir] = False
                bad_data.append(data['ref_name'])

        with open(invalid_path, 'w', encoding='utf-8') as file:
            json.dump(bad_data, file, indent=2)

    return bad_data
