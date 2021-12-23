import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from fake_headers import Headers
from opencc import OpenCC


def data2df(pokemon_data):  # data to Series and then to DataFrame
    index = ['pokemon_number', 'pokemon_name_ch', 'pokemon_name_jp',
             'pokemon_name_en', 'pokemon_types', 'pokemon_ability', 'pokemon_status']
    series = pd.Series(pokemon_data, index=index)

    return pd.DataFrame(series).T


def pokemon_number_transform(pokemon_number):  # Make 1(float) to 001(string)
    if len(str(pokemon_number)) == 1:
        return "00" + str(pokemon_number)

    elif len(str(pokemon_number)) == 2:
        return "0" + str(pokemon_number)

    else:
        return str(pokemon_number)


def pokemon_name(html, opencc):  # Catch the Pokemon English, Japanese, Chinese names
    name_position = html.find("td", {"colspan": "2"}).find_all("b")
    for i, name in enumerate(name_position):
        if i == 0:
            name_ch = opencc.convert(name.text)
        elif i == 1:
            name_jp = name.text
        else:
            name_en = name.text

    return name_ch, name_jp, name_en


def pokemon_type(html, opencc):  # Catch the Pokemon types
    types = []
    type_position = html.find_all("table", {"class": "roundy bgwhite fulltable"})
    for i, type_text in enumerate(type_position):
        if i == 1:
            for s in type_text.find_all('a'):
                types.append(opencc.convert(s['title'].replace("（属性）", "")))

    return types


def pokemon_ability(html, pokemon_number, opencc):  # Catch the Pokemon abilities
    abilities = {}
    if pokemon_number == 718:
        ability_table = html.find_all("table", {
            "style": "width: 300px; margin-left: 5px; margin-bottom: 5px;"})  # No.718 Pokemon is different, must use the different ways to catch the data
    else:
        ability_table = html.find_all("table", {"class": "roundy bgwhite fulltable"})  # All Pokemon abilities data are in this Element except No.718

    for i, text in enumerate(ability_table):
        if i == 3:
            for s, ability_position in enumerate(text.find_all("td", {"width": "50%"})):  # Distinguish the Normal ability and Hidden ability
                if s == 0:  # Normal ability
                    if len(ability_position.find_all("a")) > 1:  # Normal ability is more than 1
                        normal = []  # If more than 1, make List first and put into the empty Dictionary
                        for x in ability_position.find_all("a"):
                            normal.append(opencc.convert(x.text))

                        abilities["一般特性"] = normal

                    else:  # Normal ability is = 1
                        abilities["一般特性"] = opencc.convert(ability_position.find("a").text)
                else:  # Hidden ability
                    if pokemon_number != 718:  # No.718 doesn't have Hidden ability
                        if len(ability_position.find_all("a")) > 1:  # Hidden ability is more than 1
                            special = []  # If more than 1, make List first and put into the empty Dictionary
                            for x in ability_position.find_all("a"):
                                special.append(opencc.convert(x.text))

                            abilities["隱藏特性"] = special

                        else:  # Hidden ability is = 1
                            abilities["隱藏特性"] = opencc.convert(ability_position.find("a").text)

    return abilities


def pokemon_status(html):  # Catch the Pokemon status (HP, Attack, Defence...)
    status = {}
    status_name = ["HP", "攻擊", "防禦", "特攻", "特防", "速度", "總和"]

    status_table = html.find_all("div", {"style": "float:right"})
    for i, status_number in enumerate(status_table):
        if i <= 6:
            status[status_name[i]] = int(status_number.text)
    return status


def next_url(html):  # Make the next page's url
    url_position = html.find("td", {"class": "roundyright-25"}).find("a").get('href')

    return "https://wiki.52poke.com" + url_position


def total_pokemon(html):  # Catch the total of the Pokemon
    solditem_list = html.find("table", {"class": "fulltable at-r"}).find_all("a")
    for i in solditem_list:
        if "No." in i.text.strip():
            return int(i.text.strip().split("：")[0].replace('No.', ''))


def get_html(pokemon_url):
    header = {'user-agent': Headers(headers=False).generate()['User-Agent']}
    response = requests.get(pokemon_url, headers=header, verify=False)

    return response.text


def html_decode(html, pokemon_number, opencc):  # Decode the Html data
    now_pokemon_number_str = pokemon_number_transform(pokemon_number)
    pokemon_name_ch, pokemon_name_jp, pokemon_name_en = pokemon_name(html, opencc)
    pokemon_types = pokemon_type(html, cc)
    pokemon_abilities = pokemon_ability(html, pokemon_number, opencc)
    pokemon_status_ = pokemon_status(html)

    print("next_url : ", url)
    print("now_pokemon_number_str : ", now_pokemon_number_str)
    print("end_pokemon_number : ", end_pokemon_number)
    print("pokemon_name_ch : ", pokemon_name_ch)
    print("pokemon_name_jp : ", pokemon_name_jp)
    print("pokemon_name_en : ", pokemon_name_en)
    print("pokemon_types : ", pokemon_types)
    print("pokemon_abilities : ", pokemon_abilities)
    print("pokemon_status_ : ", pokemon_status_)
    print("=" * 100)

    return [now_pokemon_number_str, pokemon_name_ch, pokemon_name_jp,
            pokemon_name_en, pokemon_types, pokemon_abilities, pokemon_status_]


# Catch the first page's data (No.001 Bulbasaur's page)
url = "https://wiki.52poke.com/wiki/%E5%A6%99%E8%9B%99%E7%A7%8D%E5%AD%90"
cc = OpenCC('s2tw')
now_pokemon_number = 1

html_text = get_html(url)  # Catch the first page's Html (No.001 Bulbasaur's page)
soup = BeautifulSoup(html_text, 'html.parser')

url = next_url(soup)  # Make the next page's url
end_pokemon_number = total_pokemon(soup)  # Catch the total of Pokemon in first page

first_data = html_decode(soup, now_pokemon_number, cc)  # Decode the Html data (No.001 Bulbasaur's page)
data_df = data2df(first_data)  # first page's data (No.001 Bulbasaur) to DataFrame
time.sleep(random.randint(10, 15))  # Wait random seconds for finished 1 page

# Catch all of the Pokemon's page (No.002 to the total_pokemon counts)
for i in range(end_pokemon_number - 1):
    now_pokemon_number += 1
    html_text = get_html(url)
    soup = BeautifulSoup(html_text, 'html.parser')
    url = next_url(soup)

    nonfirst_data = html_decode(soup, now_pokemon_number, cc)  # Decode the Html data (No.002 to the total_pokemon counts)
    nonfirst_data_df = data2df(nonfirst_data)  # data (No.002 to the total_pokemon counts) to DataFrame
    data_df = data_df.append(nonfirst_data_df, ignore_index=True)  # New data's DataFrame bind into old data's DataFrame
    time.sleep(random.randint(10, 15))  # Wait random seconds for finished 1 page

data_df.to_csv("Pokemon1.csv", index=False)  # save the data to csv
print("本次爬蟲已經運行完畢！！")  # Finish
