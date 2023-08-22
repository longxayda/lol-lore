from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from const import URL, PARALLEL
import concurrent.futures
import os
import typing as T

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