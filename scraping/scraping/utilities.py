import os
import bs4
import json
import time
import typing as T
import concurrent.futures
import scraping.scraping.constants as constants
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

def build_path(dir: str = ''):
    path = str(os.path.dirname((os.path.realpath(__file__))))
    path = path + '/' + dir
    return path.replace('\\', '/')

def get_root_directory():
    sep_path = build_path().split('/')
    root_sep_path = sep_path[:sep_path.index(constants.PROJ_NAME) + 1]
    return '/'.join(root_sep_path)

def get_content(command: str, champion: str = '', base_url: str = constants.URL):
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
        opts.add_argument('--log-level=OFF')
        driver = webdriver.Chrome(options=opts)
        driver.get(url)
        WebDriverWait(driver, 5)
        content = driver.page_source
        driver.close()
        return content

    url = build_url()
    if url is None:
        return None
    print(url)
    return fetch(url)


def parallelize(iterables: T.Iterable, function: T.Callable, timeout: int = None, concurrency: int = constants.PARALLEL):
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
                time.sleep(2)
            else:
                break
        return output
    
def coalesce(source: T.Dict[str, str], target: T.Dict[str, str]):
    for key in target:
        value = target[key] if (target[key] or key not in source) else source[key]
        target[key] = value
    return target

def recursive_find(soup: T.Union[bs4.BeautifulSoup, bs4.Tag], pairs: T.List[T.List]):
    if soup is None:
        return None
    if not len(pairs) or not len(soup.contents) or soup.findChild(pairs[0][0]) is None:
        soup = soup.get_text() if soup.string is None else soup.string
        if soup is None:
            return None
        return soup.strip()
    soup = soup.find(*pairs[0])

    return recursive_find(soup, pairs[1:])

def validate():
    def helper(data: T.Dict[str, str]):
        ref_keys = ["name", "race", "type", "region", "quote", "ref_name", "biography"]
        res = {}
        for key in ref_keys:
            if key not in data:
                res[key] = False
            else:
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
                            if ele == '' or ele.lower() == 'read story':
                                res['biography'] = False
                                break
                else:
                    res[key] = data[key] != '' and data[key] is not None

        return [key for key in res if not res[key]]

    json_directory_path = get_root_directory() + '/output/scraping/json'
    ref_path = json_directory_path + '/champs.json'
    invalid_path = json_directory_path + '/invalid.json'
    base_path = json_directory_path + '/info'
    precise_path = base_path + '/%s/data.json'

    ref_data = []

    with open(ref_path, 'r', encoding='utf-8') as file:
        ref_data = [data['ref_name'] for data in json.load(file)]

    scrape_dirs = os.listdir(base_path)

    output = {}
        
    bad_data = []
    for champ_name in ref_data:
        if champ_name not in scrape_dirs:
            bad_data.append(champ_name)
            output[champ_name] = ['everything']

    for scrape_dir in scrape_dirs:
        current_precise_path = precise_path % scrape_dir
        if os.path.isfile(current_precise_path):
            with open(current_precise_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                missing_fields = helper(data)
                if len(missing_fields):
                    bad_data.append(scrape_dir)
                output[scrape_dir] = missing_fields 
        else:
            if '.' not in scrape_dir:
                output[scrape_dir] = ['everything']
                bad_data.append(scrape_dir)
                print(bad_data)

    with open(invalid_path, 'w', encoding='utf-8') as file:
        json.dump(bad_data, file, indent=2)

    return output
