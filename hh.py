import requests
import json
import csv
with open('hh.csv', 'a', encoding='utf-8-sig', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at'])
for page in range(20):
    req = requests.get(
        f'https://api.hh.ru/vacancies?specialization=1&date_from=2022-12-17&date_to=2022-12-17&per_page=100&page={page}')
    data = req.content.decode()
    req.close()
    js = json.loads(data)
    for item in js['items']:
        row = []
        row.append(item['name'])
        if item['salary'] == None:
            row.append(None)
            row.append(None)
            row.append(None)
        else:
            row.append(item['salary']['from'])
            row.append(item['salary']['to'])
            row.append(item['salary']['currency'])
        row.append(item['area']['name'])
        row.append(item['published_at'])
        with open('hh.csv', 'a', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)