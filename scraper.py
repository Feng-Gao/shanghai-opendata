# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import scraperwiki

#NOTE that we parse dataproduct and dataapi seperately and the dirty solution is manually replace the url and set index accordingly
#to crawl both product and api, so do not forget to set file writer method to 'a' when you work on api list
base_url = 'http://www.datashanghai.gov.cn/query!queryProduct.action?currentPage='
index = 1
#manually check on the website and set the max_index accordingly
max_index = 137

#we need random ua to bypass website security check
ua = UserAgent()
headers = {'User-Agent':ua.random}

#we create a metadata dict as it might be possible that for some dataset some metadata may be missing or in wrong order
meta_dict = {
            '摘要：':'desc',
            '应用场景：':'',
            '数据标签：':'',
            '关键字：':'tags',
            '数据领域：':'topics',
            '国家主题分类：':'',
            '部门主题分类：':'',
            '公开属性：':'',
            '更新频度：':'frequency',
            '首次发布日期：':'created',
            '更新日期：':'updated',
            '访问/下载次数：':'count',
            '数据提供方：':'org',
            '附件下载：':'',
            }

#we create a package_dict to store
package_dict = {'url':'',
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

for i in range(index,max_index+1):
    url = base_url + str(i)
    result = requests.get(taipei_url,headers=headers)
    soup = BeautifulSoup(result.content)
    #fetch all dt blocks and get rid of the first 5 as they are irrelevant
    package_blocks = soup.find_all('dt')[5:]
    for p in package_blocks:
        #for each package block on the list page, we parse the url to detail page, and package title
        package_dict['url'] = "http://www.datashanghai.gov.cn/"+p.a['href']
        package_dict['name'] = p.a['title']
        result = requests.get(package_dict['url'],headers=headers)
        #now for each package block, we fetch back its detail page and parse its metadata
        soup = BeautifulSoup(result.content)
        #there are 4 tables on detail page
        tables = soup.find_all('table')
        #the first one contains metadata
        metadata_table = table[0]
        trs =  metadata_table.find_all('tr')
        for tr in trs:
            key = re.sub('[\r\t\n ]+', '', tr.th.text)
            value = re.sub('[\r\t\n ]+', '', tr.td.text)
            if key == '访问/下载次数：':
                view,download = value.split('/')
                package_dict['count']['view'] = int(view)
                package_dict['count']['download'] = int(download)
            if key == '附件下载：':
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
                package_dict[meta_dict[key]] = value
        del package_dict['']
        scraperwiki.sqlite.save(unique_keys=['url'],data=package_dict)
