# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import scraperwiki
import datetime

import sys

reload(sys)
sys.setdefaultencoding('utf8')

#NOTE that we parse dataproduct and dataapi seperately and the dirty solution is manually replace the url and set index accordingly
#this version is for dataproduct only now
base_url = 'http://data.sh.gov.cn/query!queryProduct.action?currentPage='
index = 1
#manually check on the website and set the max_index accordingly
max_index = 137

url_list = []

for i in range(index, max_index+1):
    url_list.append(base_url+str(i))

#we need random ua to bypass website security check
ua = UserAgent()
headers = {'User-Agent':ua.random}

#we create a metadata dict as it might be possible that for some dataset some metadata may be missing or in wrong order
meta_dict = {
            '摘要：'.encode('utf-8'):'desc',
            '应用场景：'.encode('utf-8'):'',
            '数据标签：'.encode('utf-8'):'',
            '关键字：'.encode('utf-8'):'tags',
            '数据领域：'.encode('utf-8'):'topics',
            '国家主题分类：'.encode('utf-8'):'',
            '部门主题分类：'.encode('utf-8'):'',
            '公开属性：'.encode('utf-8'):'',
            '更新频度：'.encode('utf-8'):'frequency',
            '首次发布日期：'.encode('utf-8'):'created',
            '更新日期：'.encode('utf-8'):'updated',
            '访问/下载次数：'.encode('utf-8'):'count',
            '数据提供方：'.encode('utf-8'):'org',
            '附件下载：'.encode('utf-8'):'',
            }
package_count = 0
problem_list=[]

today_date = datetime.date.today().strftime("%m/%d/%Y")

for u in url_list:
    #print(u)
    result = requests.get(u,headers=headers)
    soup = BeautifulSoup(result.content,features="lxml")
    #fetch all dt blocks and get rid of the first 5 as they are irrelevant
    package_blocks = soup.find_all('dt')[5:]
    for p in package_blocks:
        #we create a package_dict to store
        package_dict = {
                'today':today_date,
                'id':0,
                'index_url':u,
                'url':'',
                'name':'',
                'desc':'',
                'org':'',
                'topics':'',
                'tags':'',
                'created':'',
                'updated':'',
                'frequency':'',
                'count':
                    {
                    'view':0,
                    'download':0
                    },
                'format':''
               }
        #for each package block on the list page, we parse the url to detail page, and package title
        package_dict['url'] = "http://www.datashanghai.gov.cn/"+p.a['href']
        package_dict['name'] = p.a['title']
        package_dict['id'] = package_count+1
        package_count += 1
       # print(package_dict['url'])
       # print(package_dict['name'])
        result = requests.get(package_dict['url'],headers=headers)
        #now for each package block, we fetch back its detail page and parse its metadata
        soup = BeautifulSoup(result.content,features="lxml")
        #there are 4 tables on detail page
        tables = soup.find_all('table')
        #the first one contains metadata
        try:
            metadata_table = tables[0]

            trs =  metadata_table.find_all('tr')
            for tr in trs:
                key = re.sub('[\r\t\n ]+', '', tr.th.text)
                value = re.sub('[\r\t\n ]+', '', tr.td.text)
                if key.encode('utf-8') == '访问/下载次数：'.encode('utf-8'):
                    view,download = value.split('/')
                    package_dict['count']['view'] = int(view)
                    package_dict['count']['download'] = int(download)
                if key.encode('utf-8') == '附件下载：'.encode('utf-8'):
                    #datashanghai only contains image-based format list on its data package
                    #we need to iterate each file's image to parse its format
                    imgs = tr.find_all(src=re.compile("images/"))
                    format = []
                    for i in imgs:
                        format.append(i['src'].split('/')[1].split('.')[0])
                    format = '|'.join(format)
                    package_dict['format'] = format
                else:
                    # for meta_dict elements that not mapped into package_dict it will create a '' key in package_dict
                    package_dict[meta_dict[key.encode('utf-8')]] = value
            del package_dict['']
            scraperwiki.sqlite.save(unique_keys=['today','id'],data=package_dict)
           # print('*******************end'+package_dict['name']+'end****************************')
        except:
            print("on"+u+"\n")
            print("add"+package_dict['url']+"into problem_list to retry")
            problem_list.append({'name':package_dict['name'],'url':package_dict['url'],'index':u})
            continue

print(problem_list)

for p in problem_list:
    #we create a package_dict to store
    package_dict = {
            'today':today_date,
            'id':0,
            'index_url':p['index'],
            'url':'',
            'name':'',
            'desc':'',
            'org':'',
            'topics':'',
            'tags':'',
            'created':'',
            'updated':'',
            'frequency':'',
            'count':
                {
                'view':0,
                'download':0
                },
            'format':''
           }
    #for each package block on the list page, we parse the url to detail page, and package title
    package_dict['url'] = "http://www.datashanghai.gov.cn/"+p['url']
    package_dict['name'] = p['name']
    package_dict['id'] = package_count+1
    package_count += 1
    #print(package_dict['url'])
    #print(package_dict['name'])
    result = requests.get(package_dict['url'],headers=headers)
    #now for each package block, we fetch back its detail page and parse its metadata
    soup = BeautifulSoup(result.content,features="lxml")
    #there are 4 tables on detail page
    tables = soup.find_all('table')
    #the first one contains metadata
    try:
        metadata_table = tables[0]

        trs =  metadata_table.find_all('tr')
        for tr in trs:
            key = re.sub('[\r\t\n ]+', '', tr.th.text)
            value = re.sub('[\r\t\n ]+', '', tr.td.text)
            if key.encode('utf-8') == '访问/下载次数：'.encode('utf-8'):
                view,download = value.split('/')
                package_dict['count']['view'] = int(view)
                package_dict['count']['download'] = int(download)
            if key.encode('utf-8') == '附件下载：'.encode('utf-8'):
                #datashanghai only contains image-based format list on its data package
                #we need to iterate each file's image to parse its format
                imgs = tr.find_all(src=re.compile("images/"))
                format = []
                for i in imgs:
                    format.append(i['src'].split('/')[1].split('.')[0])
                format = '|'.join(format)
                package_dict['format'] = format
            else:
                # for meta_dict elements that not mapped into package_dict it will create a '' key in package_dict
                package_dict[meta_dict[key.encode('utf-8')]] = value
        del package_dict['']
        scraperwiki.sqlite.save(unique_keys=['today','id'],data=package_dict)
    except:
        print("in the retry process now\n")
        print("add"+package_dict['url']+"into problem_list to retry")
        problem_list.append(package_dict['url'])
        continue
   # print('*******************end'+package_dict['name']+'end****************************')
