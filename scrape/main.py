from utils import (
    get_content, 
    build_path
)
import typing as T
import bs4
import re
import json
import os

os.makedirs(build_path('../out/json'), exist_ok=True)
os.makedirs(build_path('../out/html'), exist_ok=True)

def get_main():
    source = get_content('home')

    soup = bs4.BeautifulSoup(source, 'html.parser')
    gen: T.Generator[T.Union[bs4.NavigableString, bs4.Tag, None], None, None] = (li for li in soup.find_all('li'))

    output = []
    for li in gen:
        a = li.find('a')
        if a is not None and a.has_attr('href') and re.match(r'\/en_US\/champion\/[a-zA-Z0-9_-]+\/', a['href']):
            name = a.find('h1').string
            region = a.find('span').string
            img_ref = a.find_all('div', {"data-am-url": True}, recursive=True)[0]['data-am-url']
            output.append({
                "name": name,
                "region": region,
                "image": img_ref
            })

    with open(build_path('../out/json/champs.json'), 'w') as file:
        json.dump(output, file, indent=2)

get_main()