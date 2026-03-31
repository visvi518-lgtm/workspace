import re
import urllib.request

url = "https://bit.ly/3rxQFS4"
html = urllib.request.urlopen(url)
html_contents = str(html.read())
id_result = re.findall(r"([A-Za-z0-9]+\*\*\*)", html_contents)

for result in id_result:
    print(result)