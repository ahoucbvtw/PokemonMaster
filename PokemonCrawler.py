import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from fake_headers import Headers
from opencc import OpenCC


class Pokemon_Crawler:
    def __init__(self):
        self.result = None
        self.now_pokemon_number = 1  # Default is 1
        self.end_pokemon_number = 0  # Default is 0
        self.cc = OpenCC('s2tw')  # Change the Simplified Chinese to Traditional Chinese
        self.headers = {}
        self.url = "https://wiki.52poke.com/wiki/%E5%A6%99%E8%9B%99%E7%A7%8D%E5%AD%90" # Default is first page (No.001 Bulbasaur's page)
        self.index = ['pokemon_number', 'pokemon_name_ch', 'pokemon_name_jp',
                      'pokemon_name_en', 'pokemon_types', 'pokemon_ability', 'pokemon_status']
        
    def data2df(self, pokemon_data):  # data to Series and then to DataFrame
        series = pd.Series(pokemon_data, index=self.index)

        return pd.DataFrame(series).T    
    
    def next_url(self, html):  # Make the next page's url
        url_position = html.find("td", {"class": "roundyright-25"}).find("a").get('href')
        self.url = "https://wiki.52poke.com" + url_position

    def random_header(self):

        return {'user-agent': Headers(headers=False).generate()['User-Agent']}

    def number_change_format(self, string_number):
        string_number = string_number.replace('No.', '')

        return int(string_number)

    def nownumber_2string(self, nownumber):  # Make 1(float) to 001(string)
        if len(str(nownumber)) == 1:
            return "00" + str(nownumber)

        elif len(str(nownumber)) == 2:
            return "0" + str(nownumber)

        else:
            return str(nownumber)

    def s2tw(self, simplechinese_text):  # Change the Simplified Chinese to Traditional Chinese        
        return self.cc.convert(simplechinese_text)

    def get_html(self, url):
        requests.packages.urllib3.disable_warnings()
        self.headers = self.random_header()
        r = requests.get(url, headers=self.headers, verify=False)

        return r.text

    def total_pokemons(self, html):  # Catch the total of the Pokemon
        soup = BeautifulSoup(html, 'html.parser')
        solditem_list = soup.find("table", {"class": "fulltable at-r"}).find_all("a")

        for i in solditem_list:
            if "No." in i.text.strip():
                self.end_pokemon_number = self.number_change_format(i.text.strip().split("：")[0])

    def pokemon_name(self, html):  # Catch the Pokemon English, Japanese, Chinese names
        name_position = html.find("td", {"colspan": "2"}).find_all("b")
        for i, name in enumerate(name_position):
            if i == 0:
                name_ch = self.s2tw(name.text)

            elif i == 1:
                name_jp = name.text
            else:
                name_en = name.text

        return name_ch, name_jp, name_en

    def pokemon_type(self, html):  # Catch the Pokemon types
        types = []
        type_position = html.find_all("table", {"class": "roundy bgwhite fulltable"})
        for i, text in enumerate(type_position):
            if i == 1:
                for s in text.find_all('a'):
                    types.append(self.s2tw(s['title'].replace("（属性）", "")))

        return types

    def pokemon_ability(self, html):  # Catch the Pokemon abilities
        abilities = {}
        if self.now_pokemon_number == 718:
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
                                normal.append(self.s2tw(x.text))

                            abilities["一般特性"] = normal

                        else:  # Normal ability is = 1
                            abilities["一般特性"] = self.s2tw(ability_position.find("a").text)
                    else:  # Hidden ability
                        if self.now_pokemon_number != 718:  # No.718 doesn't have Hidden ability
                            if len(ability_position.find_all("a")) > 1:  # Hidden ability is more than 1
                                special = []  # If more than 1, make List first and put into the empty Dictionary
                                for x in ability_position.find_all("a"):
                                    special.append(self.s2tw(x.text))

                                abilities["隱藏特性"] = special

                            else:  # Hidden ability is = 1
                                abilities["隱藏特性"] = self.s2tw(ability_position.find("a").text)

        return abilities

    def pokemon_status(self, html):  # Catch the Pokemon status (HP, Attack, Defence...)
        status = {}
        status_name = ["HP", "攻擊", "防禦", "特攻", "特防", "速度", "總和"]
        status_table = html.find_all("div", {"style": "float:right"})
        for i, status_number in enumerate(status_table):
            if i <= 6:
                status[status_name[i]] = int(status_number.text)

        return status

    def html_decode(self, html):  # Decode the Html data
        soup = BeautifulSoup(html, 'html.parser')
        self.next_url(soup)
        pokemon_number = self.nownumber_2string(self.now_pokemon_number)
        pokemon_name_ch, pokemon_name_jp, pokemon_name_en = self.pokemon_name(soup)
        pokemon_types = self.pokemon_type(soup)

        try:
            pokemon_abilities = self.pokemon_ability(soup)
        except:
            pokemon_abilities = dict()

        pokemon_status_ = self.pokemon_status(soup)

        print("pokemon_number : ", pokemon_number)
        print("pokemon_name_ch : ", pokemon_name_ch)
        print("pokemon_name_jp : ", pokemon_name_jp)
        print("pokemon_name_en : ", pokemon_name_en)
        print("pokemon_types : ", pokemon_types)
        print("pokemon_abilities : ", pokemon_abilities)
        print("pokemon_status_ : ", pokemon_status_)
        print("=" * 150)
        
        return [pokemon_number, pokemon_name_ch, pokemon_name_jp, pokemon_name_en,
                pokemon_types, pokemon_abilities, pokemon_status_]

    def start_crawler(self):
        html_text = self.get_html(self.url)  # Catch the first page's Html (No.001 Bulbasaur's page)
        self.total_pokemons(html_text)  # Catch the total of Pokemon in first page
        print("total_pokemon : ", self.end_pokemon_number)
        print("=" * 150)

        first_data = self.html_decode(html_text)  # Decode the Html data (No.001 Bulbasaur's page)
        self.result = self.data2df(first_data)  # first page's data (No.001 Bulbasaur) to DataFrame
        self.now_pokemon_number += 1  # Make the next page url
        time.sleep(random.randint(10, 15))  # Wait random seconds for finished 1 page

        for i in range(self.end_pokemon_number - 1):  # Catch all of the Pokemon's page (No.002 to the total_pokemon counts)
            html_text = self.get_html(self.url)
            nonfitst_data = self.html_decode(html_text)  # Decode the Html data (No.002 to the total_pokemon counts)
            nonfitst_data_df = self.data2df(nonfitst_data)  # data (No.002 to the total_pokemon counts) to DataFrame
            self.result = self.result.append(nonfitst_data_df, ignore_index=True)  # New data's DataFrame bind into old data's DataFrame
            self.now_pokemon_number += 1
            
            if i != (self.end_pokemon_number - 2):  # The last page can pass wait seconds
                time.sleep(random.randint(10, 15))

        self.result.to_csv("Pokemon.csv", index=False)  # save the data to csv


if __name__ == "__main__":
    pokemon = Pokemon_Crawler()
    pokemon.start_crawler()

    print("本次爬蟲已經運行完畢！！")  # Finish
