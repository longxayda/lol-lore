import os
import re
import sys
import bs4
import json
import typing as T
import scraping.scraping.utilities as utilities

ROOT_DIRECTORY = utilities.get_root_directory()
OUTPUT_DIRECTORY = ROOT_DIRECTORY + '/output/scraping'

JSON_DIRECTORY_PATH = OUTPUT_DIRECTORY + '/json'
HTML_DIRECTORY_PATH = OUTPUT_DIRECTORY + '/html'

os.makedirs(JSON_DIRECTORY_PATH + '/info', exist_ok=True)
os.makedirs(HTML_DIRECTORY_PATH, exist_ok=True)

def get_main() -> T.List[T.Dict[str, str]]:
    source = utilities.get_content('home')
    json_path = JSON_DIRECTORY_PATH + '/champs.json'
    html_path = HTML_DIRECTORY_PATH + '/champs.html'
    soup = bs4.BeautifulSoup(source, 'html.parser')
    gen: T.Generator[T.Union[bs4.NavigableString, bs4.Tag, None], None, None] = (li for li in soup.find_all('li'))
    
    with open(html_path, 'w') as file:
        file.write(str(soup.prettify()))

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

    print(len(output))
    return output

def get_champ(data: T.Dict) -> T.List[T.Dict[str, str]]:
    search_name = data['ref_name']
    
    json_directory_path = JSON_DIRECTORY_PATH + f'/info/{search_name}'
    html_directory_path = HTML_DIRECTORY_PATH + f'/{search_name}'
    html_path = html_directory_path + '/info.html'
    json_path = json_directory_path + '/info.json'
    
    source = utilities.get_content('champion', search_name)
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

    champ_race = utilities.recursive_find(soup, [['div', {'class': re.compile(patterns['race'])}], ['h6']])
    champ_quote = utilities.recursive_find(soup, [['li', {'class': re.compile(patterns['quote'])}], ['p']])
    champ_type = utilities.recursive_find(soup, [['div', {'class': re.compile(patterns['type'])}], ['h6']])
    champ_name = utilities.recursive_find(soup, [['div', {'class': re.compile(patterns['name'])}], ['span']])
    champ_region = utilities.recursive_find(soup, [['div', {'class': re.compile(patterns['region'])}], ['h6'], ['span']])
    champ_biography_text = utilities.recursive_find(soup, [['div', {'class': re.compile(patterns['biography_text'])}], ['p']])

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

        output = utilities.coalesce(temp, output)
    
    with open(json_path, 'w') as file:
        json.dump(output, file, indent=2)

    return output
    

def get_lore(data: T.Dict[str, str]) -> T.Dict[str, str]:
    search_name = data['ref_name']

    json_directory_path = JSON_DIRECTORY_PATH + f'/info/{search_name}'
    html_directory_path = HTML_DIRECTORY_PATH + f'/{search_name}'
    html_path = html_directory_path + '/lore.html'
    json_path = json_directory_path + '/lore.json'

    source = utilities.get_content('story', search_name)
    soup = bs4.BeautifulSoup(source, 'html.parser')

    os.makedirs(html_directory_path, exist_ok=True)

    with open(html_path, 'w') as file:
        file.write(str(soup.prettify()))

    pattern = r'content_(.*)?'
        
    paragraphs_outer = soup.find('div', {'class': re.compile(pattern)})
    
    paragraphs = paragraphs_outer.find_all('p')
    
    if not len(paragraphs):
        paragraphs = paragraphs_outer.find_all('div')
        
    new_paragraphs = []
    for paragraph in paragraphs:
        paragraph: bs4.Tag = paragraph
        value: str = paragraph.string if paragraph.string else paragraph.get_text()
        if value:
            new_paragraphs.append(value)

    if os.path.isfile(json_path):
        with open(json_path, 'r', encoding='utf-8') as file:
            temp = json.load(file)
    else:
        temp = {}
    
    output = {'biography': new_paragraphs}

    os.makedirs(json_directory_path, exist_ok=True)

    output = utilities.coalesce(temp, output)
    
    with open(json_path, 'w') as file:
        json.dump(output, file, indent=2)
    
    return output

def get_champ_full_info(data: T.Dict[str, str]):
    champ_info = get_champ(data)
    champ_lore = get_lore(data)
    search_name = data["ref_name"]
    json_path = JSON_DIRECTORY_PATH + f'/info/{search_name}/data.json'
    output = {**champ_info, **champ_lore}
    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump(output, file, indent=2)
    return output

def run():
    champs_path = JSON_DIRECTORY_PATH + '/champs.json'
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

    output = set()
    
    if len(sys.argv) > 1:
        champ_names = sys.argv[1:]
        for champ_name in champ_names:
            found = False
            for champ in champs:
                if champ['name'].lower() == champ_name or champ['ref_name'] == champ_name.lower():
                    output.add(get_champ_full_info(champ)['ref_name'])
                    found = True
                    break

            if not found:
                print('No champion named %s' % champ_name)

    else:
        retries = 10
        invalid_path = JSON_DIRECTORY_PATH + '/invalid.json'
        while len(champs) and retries:
            validation_result = utilities.validate()
            print("Validation result:")
            for key in validation_result:
                if validation_result[key]:
                    print('\t', key, ':', validation_result[key])
            bad_champs = {champ['ref_name'] for champ in champs}
            if os.path.isfile(invalid_path):
                with open(invalid_path, 'r', encoding='utf-8') as file:
                    bad_champs = {data for data in json.load(file)}
            
            print('List of target champs:', list(bad_champs))
            champs = list(filter(lambda champ: champ['ref_name'] in bad_champs, champs))
            print('Number of retries left:', retries)
            result = utilities.parallelize(champs, get_champ_full_info, 120)
            output.update([record['ref_name'] for record in result])
            retries -= 1
    
    return list(output)

