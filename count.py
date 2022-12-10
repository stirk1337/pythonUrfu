from notmain import DataSet
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
import requests

filename = "year_big.csv"
vac, header = DataSet.csv_reader(filename)
vac = DataSet.csv_filer(vac)

currencies = {}

for item in vac:
    for i in range(len(item)):
        if header[i] == "salary_currency":
            if item[i] not in currencies:
                currencies[item[i]] = 0
            currencies[item[i]] += 1

new_vac = []
for item in vac:
    for i in range(len(item)):
        if header[i] == "salary_currency":
            if currencies[item[i]] >= 5000:
                new_vac.append(item)

old = datetime(2022, 12, 1)
new = datetime(2000, 1, 1)
currencies = {k: v for k, v in currencies.items() if v >= 5000}

for item in new_vac:
    for i in range(len(item)):
        if header[i] == "published_at":
            data = item[i].split('-')
            y, m = int(data[0]), int(data[1])
            date = datetime(y, m, 1)
            if date < old:
                old = date
            if date > new:
                new = date

data = {}
index = []

for i in range(old.year, new.year + 1):
    for j in range(1, 12 + 1):
        month = j
        if month < 10:
            month = "0" + str(j)
        URL = f"http://www.cbr.ru/scripts/XML_daily.asp?date_req=02/{month}/{i}"
        response = requests.get(URL)
        with open('XML_daily.xml', 'wb') as file:
            file.write(response.content)
        tree = ET.parse('XML_daily.xml')
        root = tree.getroot()
        found = list(currencies.keys())
        for child in root:
            nominal = 0
            value = 0
            curr = 0
            skip = False
            for child2 in child:
                if child2.tag == "CharCode" and child2.text not in currencies:
                    skip = True
                    continue
                if child2.tag == 'Nominal':
                    nominal = float(child2.text)
                if child2.tag == 'Value':
                    value = float(child2.text.replace(",", "."))
                if child2.tag == 'CharCode':
                    curr = child2.text
            if skip:
                continue
            enter = value / nominal
            if curr not in data:
                data[curr] = []
            data[curr].append(enter)
            found.remove(curr)
        index.append(f"{i}-{month}")
        for f in found:
            if f not in data:
                data[f] = []
            data[f].append(0)

df = pd.DataFrame(data=data, index=index)
print(df)