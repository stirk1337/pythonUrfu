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
data2 = {
    "name": [],
    "salary": [],
    "area_name": [],
    "published_at": [],
}

for item in new_vac:
    for i in range(len(item)):
        if header[i] == "name":
            name = item[i]
        if header[i] == "salary_from":
            salary_from = float(item[i])
        if header[i] == "salary_to":
            salary_to = float(item[i])
        if header[i] == "salary_currency":
            salary_currency = item[i]
        if header[i] == "area_name":
            area_name = item[i]
        if header[i] == "published_at":
            published_at = item[i]
    year = published_at.split('-')[0]
    month = published_at.split('-')[1]
    date = year + "-" + month
    salary = (salary_from + salary_to) / 2
    if salary_currency != "RUR":
        course = df.loc[date,  salary_currency]
        if course == 0:
            continue
        salary *= course
    data2["name"].append(name)
    data2["salary"].append(salary)
    data2["area_name"].append(area_name)
    data2["published_at"].append(published_at)

df2 = pd.DataFrame(data=data2)

pd.options.display.max_columns = 10
print(df)
print(df2)

with open('csv_data.txt', 'w', encoding="utf-8-sig", newline="") as csv_file:
    df2.head(100).to_csv(path_or_buf=csv_file, index=False)