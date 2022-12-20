from notmain import DataSet
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
import sqlite3

filename = "year_big.csv"
vac, header = DataSet.csv_reader(filename)
vac = DataSet.csv_filer(vac)
df = pd.DataFrame(data=vac, columns=header)
currencies = {}

for index, row in df.iterrows():
    if row['salary_currency'] not in currencies:
        currencies[row['salary_currency']] = 0
    currencies[row['salary_currency']] += 1

drops = []
for index, row in df.iterrows():
    if not currencies[row['salary_currency']] >= 5000:
        drops.append(index)
df.drop(drops, axis=0, inplace=True)
old = datetime(2022, 12, 1)
new = datetime(2000, 1, 1)
currencies = {k: v for k, v in currencies.items() if v >= 5000}

for index, row in df.iterrows():
    data = row['published_at'].split('-')
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

cr = pd.DataFrame(data=data, index=index)

conn = sqlite3.connect('centrobank')
c = conn.cursor()
cr.to_sql('currencies', conn, if_exists='replace', index='valute')

salaries = []
for index, row in df.iterrows():
    year = row['published_at'].split('-')[0]
    month = row['published_at'].split('-')[1]
    date = year + "-" + month
    salary = (float(row['salary_from']) + float(row['salary_to'])) / 2
    if row['salary_currency'] != "RUR":
        c.execute(f"""
        SELECT {row['salary_currency']} FROM CURRENCIES WHERE valute='{date}'
        """)
        course = c.fetchall()
        course = float(course[0][0])
        salary *= course
    salaries.append(salary)
df.pop('salary_from')
df.pop('salary_currency')
df.pop('salary_to')
df['salary'] = salaries

pd.options.display.max_columns = 10
print(df)

with open('csv_data.txt', 'w', encoding="utf-8-sig", newline="") as csv_file:
    df.head(100).to_csv(path_or_buf=csv_file, index=False)