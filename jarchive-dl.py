import requests, pprint, json, time, datetime
import dateutil.parser as parser
from collections import defaultdict
from bs4 import BeautifulSoup

BASE_URL = "http://www.j-archive.com/showgame.php"

def substring_in_list(substring, list_):
    return any(substring in string for string in list_)

def get_clue_text(htmlnode):
    clue_text_node = htmlnode.find('td', class_='clue_text')
    if clue_text_node is None:
        return None
    has_media = clue_text_node.find('a')
    url = has_media['href'] if has_media is not None else None
    return { 'text': clue_text_node.text, 'url': url }

def get_clue_answer(htmlnode):
    clue_answer_div = htmlnode.find('div')
    if clue_answer_div is None:
        return None
    else:
        ems = BeautifulSoup(htmlnode.find('div')['onmouseover'], 'html.parser').find_all('em')
        for em in ems:
            if substring_in_list('correct_response', em['class']):
                return em.text
        return em.text

def default_entry():
    return {}

def parse_show_metadata(metadata):
    shownum = metadata.split('-')[0].strip().split("#")[-1]
    datestr_raw = metadata.split('-')[-1].strip()
    datetime_raw = datetime.datetime.fromisoformat(parser.parse(datestr_raw).isoformat())
    
    datestr = datetime_raw.date().isoformat()
    return {"show_num": shownum, "date": datestr}

def parse_game(game_id, jdict):
    url = BASE_URL + f"?game_id={game_id}"
    round_list = [{"idx": 0, "name": "Jeopardy", "id": "jeopardy_round"}, {"idx": 1, "name": "Double Jeopardy", "id": "double_jeopardy_round"}, {"idx": 2, "name": "Final Jeopardy", "id": "final_jeopardy_round"}]
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    metadata_str = soup.find(id="game_title").find("h1").text
    show_metadata = parse_show_metadata(metadata_str)


    for round_node in round_list:
        round = soup.find(id=round_node['id'])
        clues = round.find_all('td', class_='clue')
        categories = round.find_all('td', class_='category_name')
        num_categories = len(categories)

        clue_num = 0
        for clue in clues:
            clue_num += 1
            
            if clue is None:
                continue

            clue_obj = get_clue_text(clue)

            if round_node['id'] == "final_jeopardy_round":
                cat = round.find('td', class_='category')
                clue_answer = get_clue_answer(cat)
            else:
                clue_answer = get_clue_answer(clue)

            if clue_obj is None or clue_answer is None:
                continue
            
            entry = {
                "clue": clue_obj,
                "category": categories[clue_num % num_categories - 1].text.lower(),
                "round": round_node['name'],
                "show": show_metadata,
                "source": { "game_id": game_id, "url": url}
            }
            jdict[clue_answer]['Definitions'].append(entry)

def main():
    jdict = defaultdict(lambda: defaultdict(list))
    parse_game(9,jdict)

    #for game_id in range(1,10):
    #    #print(f"Parsing game {game_id}...")
    #    parse_game(game_id, jdict)

    print(json.dumps(jdict,indent=2))

if __name__ == "__main__":
    main()
