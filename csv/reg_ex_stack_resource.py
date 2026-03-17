import urllib.request
import re

url = "https://finance.naver.com/item/main.naver?code=005930"
html = urllib.request.urlopen(url)
html_contents = str(html.read().decode())
#print(html_contents)

stock_result = re.findall("(\<dl class=\"blind\"\>)([\s\S]+?)(\<\/dl\>)", html_contents)

#print(stock_result)
samsung_stock = stock_result[0]
#print(samsung_stock)
samsung_index = samsung_stock[1]
#print(samsung_index)
index_list = re.findall("(\<dd\>)([\s\S]+?)(\<\/dd/\>)", samsung_index)
print(len(stock_result))
#for index in index_list:
    #print (index[1])
