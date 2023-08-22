from utils import (
    get_content, 
    build_path,
    parallelize,
    coalesce,
    validate
)
import typing as T
import bs4
import re
import json
import os
import sys


os.makedirs(build_path('../out/json'), exist_ok=True)
os.makedirs(build_path('../out/html'), exist_ok=True)



def get_main() -> T.List[T.Dict[str, str]]:
    source = get_content('home')
    json_path = build_path('../out/json/champs.json')
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
                "image": img_ref,
                "ref_name": a['href'].split('/')[-2]
            })

    with open(json_path, 'w') as file:
        json.dump(output, file, indent=2)

    return output

def get_champ(data: T.Dict) -> T.List[T.Dict[str, str]]:
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
            

    search_name = data['ref_name']

    html_path = build_path(f'../out/html/{search_name}/info.html')
    json_directory_path = build_path(f'../out/json/info/{search_name}')
    html_directory_path = build_path(f'../out/html/{search_name}')
    json_path = build_path(f'../out/json/info/{search_name}/info.json')
    source = get_content('champion', search_name)
    soup = bs4.BeautifulSoup(source, 'html.parser')

    os.makedirs(html_directory_path, exist_ok=True)

    with open(html_path, 'w') as file:
        file.write(str(soup.prettify()))

    patterns = {
        'race': r'race_[a-zA-Z0-9]+',
        'name': r'titles_[a-zA-Z0-9]+',
        'quote': r'quote_[a-zA-Z0-9]+',
        'type': r'typeDescription_[a-zA-Z0-9]+',
        'biography_text': r'biographyText_[a-zA-Z0-9]+',
        'region': r'factionName_[a-zA-Z0-9]+',
    }

    champ_race = recursive_find(soup, [['div', {'class': re.compile(patterns['race'])}], ['h6']])
    champ_quote = recursive_find(soup, [['li', {'class': re.compile(patterns['quote'])}], ['p']])
    champ_type = recursive_find(soup, [['div', {'class': re.compile(patterns['type'])}], ['h6']])
    champ_name = recursive_find(soup, [['div', {'class': re.compile(patterns['name'])}], ['span']])
    champ_region = recursive_find(soup, [['div', {'class': re.compile(patterns['region'])}], ['h6'], ['span']])
    champ_biography_text = recursive_find(soup, [['div', {'class': re.compile(patterns['biography_text'])}], ['p']])

    output = {
        'name': champ_name,
        'race': champ_race,
        'type': champ_type,
        'region': champ_region,
        'quote': champ_quote[1:-1] if champ_quote else champ_quote,
        'biography_text': champ_biography_text,
        'ref_name': search_name
    }
    
    os.makedirs(json_directory_path, exist_ok=True)

    if os.path.isfile(json_path):
        with open(json_path, 'r', encoding='utf-8') as file:
            temp = json.load(file)

        output = coalesce(temp, output)
    
    with open(json_path, 'w') as file:
        json.dump(output, file, indent=2)

    return output
    

def get_lore(data: T.Dict[str, str]) -> T.Dict[str, str]:
    search_name = data['ref_name']

    html_path = build_path(f'../out/html/{search_name}/lore.html')
    json_directory_path = build_path(f'../out/json/info/{search_name}')
    html_directory_path = build_path(f'../out/html/{search_name}')
    json_path = build_path(f'../out/json/info/{search_name}/lore.json')
    source = get_content('story', search_name)
    soup = bs4.BeautifulSoup(source, 'html.parser')

    os.makedirs(html_directory_path, exist_ok=True)

    with open(html_path, 'w') as file:
        file.write(str(soup.prettify()))

    pattern = r'content_(.*)?'

    paragraphs = [
        p for p in soup.find('div', {'class': re.compile(pattern)}).find_all(['p', 'div']) 
        if p.string or p.get_text() is not None
    ]

    for idx, paragraph in enumerate(paragraphs):
        value = paragraph.string if paragraph.string else paragraph.get_text()
        paragraphs[idx] = value

    if os.path.isfile(json_path):
        with open(json_path, 'r', encoding='utf-8') as file:
            temp = json.load(file)
    else:
        temp = {}
    
    output = {'biography': paragraphs}

    os.makedirs(json_directory_path, exist_ok=True)

    output = coalesce(temp, output)
    
    with open(json_path, 'w') as file:
        json.dump(output, file, indent=2)
    
    return output

def get_champ_full_info(data: T.Dict[str, str]):
    champ_info = get_champ(data)
    champ_lore = get_lore(data)
    search_name = data["ref_name"]
    json_path = build_path(f'../out/json/info/{search_name}/data.json')
    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump({**champ_info, **champ_lore}, file, indent=2)
    return champ_lore

if __name__ == '__main__':
    
    champs_path = build_path('../out/json/champs.json')
    if os.path.isfile(champs_path):
        with open(champs_path, 'r', encoding='utf-8') as file:
            champs = json.load(file)
    else:
        champs = get_main()
    
    retries = 5
    while True:
        if not len(champs):
            champs = get_main()
        else:
            break
        if not retries:
            raise Exception('Cannot fetch champions')
        retries -= 1

    if len(sys.argv) > 1:
        champ_name = sys.argv[1]
        output = []
        for champ in champs:
            if champ['name'].lower() == champ_name or champ['ref_name'] == champ_name.lower():
                output.append(get_champ_full_info(champ))
                break
    else:
        retries = 5
        invalid_path = build_path('../out/json/invalid.json')
        while len(champs) and retries:
            validate()
            bad_champs = {champ['ref_name'] for champ in champs}
            if os.path.isfile(invalid_path):
                with open(invalid_path, 'r', encoding='utf-8') as file:
                    bad_champs = {data['ref_name'] for data in json.load(file)}
            
            print('List of error champs:', list(bad_champs))
            champs = list(filter(lambda champ: champ['ref_name'] in bad_champs, champs))
            print('Number of retries left:', retries)
            output = parallelize(champs, get_champ_full_info, 120)
            retries -= 1

