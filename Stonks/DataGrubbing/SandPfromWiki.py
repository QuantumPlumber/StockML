from bs4 import BeautifulSoup
import urllib3
import certifi

def get_SandP500():
    wiki = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    header = {'User-Agent': 'Mozilla/5.0'}  # Needed to prevent 403 error on Wikipedia

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    page = http.urlopen(method='GET', url=wiki, headers=header)
    soup = BeautifulSoup(page.data)

    symbol = []
    security = []
    sec_filing = []
    gics_sector = []
    gics_sub_sector = []
    gics_sub_industry = []
    headquarters_location = []
    date_first_added = []
    cik = []
    founded = []

    table = soup.find("table", {"class": "wikitable sortable"})
    # print(table)

    for row in table.findAll("tr"):
        #print('row:')
        #print(row)

        if len(row.findAll('th')) > 0:
            continue

        cells = row.findAll("td")
        #print('cells:')
        #print(cells)
        if len(cells) > 1:
            # for cell in cells:
            #    print(cell.find(text=True))
            # For each "tr", assign each "td" to a variable.
            symbol.append(cells[0].find(text=True))

    return symbol

if __name__ == "__main__":
    symbol = get_SandP500()
    #print(symbol)