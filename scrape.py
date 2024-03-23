#!/usr/bin/env python3

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
from typing import Set

def createDriver():
    opts = Options()
    opts.add_argument('-headless')
    return webdriver.Firefox(options=opts)


class OtodomScraper:
    def __init__(self):
        self._domain = 'https://www.otodom.pl'
        self._driver = createDriver()

    def scrape(self, query:str):
        listingLinks = set()

        try:
            page = 1
            while True:
                pageLinks = self._scrapePage(query, page)
                listingLinks |= pageLinks

                page += 1
        except StopIteration:
            pass

        return set([self._domain + l for l in listingLinks])

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self._driver.close()

    def _scrapePage(self, query:str, page:int):
        self._driver.get(f"{query}&daysSinceCreated=7&limit=72&page={page}")
        self._keepScrolling()

        soup = BeautifulSoup(self._driver.page_source, 'html.parser')
        organicResults = soup.find("div", {"data-cy":"search.listing.organic"})
        if organicResults is None:
            raise StopIteration()

        listingLinks = []
        for item in organicResults.find_all("div", {"data-cy": "listing-item"}):
            link = item.find("a")
            listingLinks.append(link['href'])

        return set(listingLinks)

    def _keepScrolling(self):
        assert self._driver is not None

        # Get scroll height
        last_height = self._driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(0.5)

            # Calculate new scroll height and compare with last scroll height
            new_height = self._driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height


class NieruchomosciOnlineScraper:
    def __init__(self):
        self._driver = createDriver()
        pass

    def __enter__(self):
        print("Beginning scraping of nieruchomosci-online")
        return self

    def __exit__(self, t, v, tb):
        print("Finished scraping of nieruchomosci-online")
        self._driver.close()

    def scrape(self, query):
        listingLinks = set()

        try:
            page = 1
            while True:
                pageLinks, stop = self._scrapePage(query, page)
                if len(pageLinks) == 0:
                    raise StopIteration()
                listingLinks |= pageLinks

                if stop:
                    raise StopIteration()

                page += 1
        except StopIteration:
            pass

        return listingLinks

    def _scrapePage(self, query, page):
        print(f"Scraping page {page} of {query}")

        listingLinks = []
        stop = False

        self._driver.get(f"{query}&p={page}")
        soup = BeautifulSoup(self._driver.page_source, 'html.parser')
        tiles = soup.find("div", {"id": "tilesWrapper"})
        assert tiles is not None
        for tile in tiles:
            if tile.name == 'div' and tile.has_attr('class'):
                if 'column-container' in tile['class']:
                    nameHolders = tile.find_all("h2", {"class":"name"})
                    for holder in nameHolders:
                        link = holder.find("a")
                        listingLinks.append(link['href'])
            elif tile.name == 'h2':
                if tile['id'] == 'pie_searchSupplement':
                    stop = True
                    break

        return set(listingLinks), stop


class GratkaScraper:
    def __init__(self):
        self._driver = createDriver()

    def scrape(self, query:str):
        listingLinks = set()

        try:
            page = 1
            while True:
                pageLinks = self._scrapePage(query, page)
                listingLinks |= pageLinks

                page += 1
        except StopIteration:
            pass

        return set(listingLinks)

    def __enter__(self):
        print("Beginning scraping of gratka")
        return self

    def __exit__(self, t, v, tb):
        print("Finished scraping of gratka")
        self._driver.close()

    def _scrapePage(self, query:str, page:int):
        print(f"Scraping page {page} of {query}")
        self._driver.get(f"{query}&page={page}")

        soup = BeautifulSoup(self._driver.page_source, 'html.parser')
        results = soup.find_all("a", {"class":"teaserLink"})
        if not results:
            raise StopIteration()

        listingLinks = []
        for item in results:
            print(item['href'])
            listingLinks.append(item['href'])

        return set(listingLinks)


class Persistence:
    def __init__(self, seenFile:str, watchFile:str):
        self._seenFile = seenFile
        self._watchFile = watchFile

    def update(self, offers:Set[str]):
        seenOffers = set()

        try:
            with open(self._seenFile, "r") as seenFile:
                seenOffers = set([l.strip() for l in seenFile.readlines()])
        except FileNotFoundError:
            pass
            
        newOffers = offers - seenOffers
        with open(self._seenFile, "a") as seenFile:
            seenFile.writelines([l + '\n' for l in newOffers])

        newOffers = [o for o in newOffers if self._filter(o)]
        with open(self._watchFile, "a") as watchFile:
            watchFile.writelines([l + '\n' for l in newOffers])

        return newOffers

    def _filter(self, link):
        for s in ['grabie', 'tyniec', 'huta', 'skawina', 'zielonki', 'bielany', \
                  'sygneczow', 'giebultow', 'kozmice', 'piekary', 'rzaska', 'szyce', \
                  'wielka-wies', 'maslomiaca', 'michalowice', 'zabierzow', 'modlniczka', \
                  'gorna-wies', 'zelkow', 'konary', 'bronowice', 'michalowice', \
                  'batowice', 'gaj', 'bosutow', 'kryspinow', 'zabawa', 'mogiany',\
                  'rusiecki', 'mogilany', 'maciejowice', 'cholerzyn', 'tomaszkowice',\
                  'tomaszowice', 'bibice', 'lusina', 'rzeszotary', 'sciejowice', \
                  'modlnica', 'baranowka', 'dojazdow', 'grebalow']:
            if s in link:
                return False

        return True

            

if __name__ == "__main__":
    SEEN_FILE = "seen.txt"
    WATCH_FILE = "watch.txt"
    OTODOM_QUERIES = [
        'https://www.otodom.pl/pl/wyniki/sprzedaz/dom/wiele-lokalizacji?ownerTypeSingleSelect=ALL&distanceRadius=0&locations=%5Bmalopolskie%2Fkrakow%2Fkrakow%2Fkrakow%2Cmalopolskie%2Fwielicki%2Fwieliczka%2Fsledziejowice%2Cmalopolskie%2Fwielicki%2Fwieliczka%2Fczarnochowice%2Cmalopolskie%2Fwielicki%2Fwieliczka%2Cmalopolskie%2Fkrakowski%2Fskawina%5D&priceMax=1700000&areaMin=70&areaMax=170&viewType=listing',
        'https://www.otodom.pl/pl/wyniki/sprzedaz/inwestycja/wiele-lokalizacji?distanceRadius=0&limit=36&priceMax=1400000&locations=%5Bmalopolskie%2Fwielicki%2Fwieliczka%2Cmalopolskie%2Fkrakowski%2Fskawina%2Cmalopolskie%2Fkrakow%2Fkrakow%2Fkrakow%2Cmalopolskie%2Fwielicki%2Fwieliczka%2Fczarnochowice%2Cmalopolskie%2Fwielicki%2Fwieliczka%2Fsledziejowice%5D&investmentEstateType=HOUSES&by=DEFAULT&direction=DESC&viewType=listing',
    ]
    NO_QUERIES = [
        'https://wieliczka.nieruchomosci-online.pl/szukaj.html?3,dom,sprzedaz,,Wieliczka:32080,,,,-1700000,-150&q=gara%C5%BC',
        'https://www.nieruchomosci-online.pl/szukaj.html?3,dom,sprzedaz,,Krak%C3%B3w:5600,,,,-1700000,-150&q=gara%C5%BC',
        'https://www.nieruchomosci-online.pl/szukaj.html?3,mieszkanie,sprzedaz,,Wieliczka:32080,,,,-1300000,75,,,,,,4,,4,,,1,,,,,,1&q=gara%C5%BC',
    ]
    GRATKA_QUERIES = [
        'https://gratka.pl/nieruchomosci/domy?typ-budynku[0]=wolnostojacy&typ-budynku[1]=blizniak&typ-budynku[2]=szeregowy&typ-budynku[3]=szeregowy-segment&stan-dom[0]=wykonczony&stan-dom[1]=do-wykonczenia&stan-dom[2]=do-remontu&stan-dom[3]=stan-surowy-zamkniety&powierzchnia-w-m2:max=170&powierzchnia-w-m2:min=70&cena-calkowita:max=1700000&rok-budowy:min=2000&lokalizacja[0]=34933&lokalizacja[1]=86187&lokalizacja[2]=86237&lokalizacja[3]=86233&lokalizacja[4]=86205&lokalizacja[5]=34749'
    ]

    offers = set()

    if OTODOM_QUERIES:
        with OtodomScraper() as scraper:
            for query in OTODOM_QUERIES:
                print(query)
                offers |= scraper.scrape(query)

    if NO_QUERIES:
        with NieruchomosciOnlineScraper() as scraper:
            for query in NO_QUERIES:
                print(query)
                offers |= scraper.scrape(query)

    if GRATKA_QUERIES:
        with GratkaScraper() as scraper:
            for query in GRATKA_QUERIES:
                print(query)
                offers |= scraper.scrape(query)

    persistence = Persistence(SEEN_FILE, WATCH_FILE)
    offersUpdated = persistence.update(offers)

    print(f"Recorded {len(offersUpdated)} new offers")

    
