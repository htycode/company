'''
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\selenum\AutomationProfile"
抓取信息:
    地区  行业  联系人  电话（手机号和座机号分开）

手机:
    已绑定手机: <span class="li02ok" title="手机号码：17762427425">手机已认证</span>
    未绑定手机: <span class="li02no" title="手机未认证">手机未认证</span>
    页面底部手机号: 没有用,不真实,为统一手机号

'''
import re
import sys
import json

import pymysql
import requests
from bs4 import BeautifulSoup

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    # 'Cookie': 'ASP.NET_SessionId=kzbhms11lkhh5xge0lzw2ly0; Hm_lvt_62c73c53c0ae8c986919225c11b0ff19=1591934094; __jsluid_h=2e43e5c8c22554578e4c4c462a2437c0; Hm_lpvt_62c73c53c0ae8c986919225c11b0ff19=1591945467',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
}
def write_to_txt(info):
    file = r'log\无联系方式.txt'
    with open(file, 'a+') as f:
        f.write(info+'\n')

# 数据库: 查询分类数据
def get_sort():
    # 链接数据库
    db = pymysql.connect(host="rm-bp1278x3bc1a6ujve1o.mysql.rds.aliyuncs.com", user="test_0527",passwd="test_0527",db="test_0527")
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 执行sql语句
    cursor.execute("select * from bfzyw_sort where is_using is Null limit 1")
    # 获取所有记录
    results = cursor.fetchall()
    cursor.execute("UPDATE bfzyw_sort SET is_using = 1 WHERE id = {}".format(results[0][0]))
    print(results)
    # 打印数据
    db.commit()
    cursor.close()  # 关闭连接
    return ({"id":results[0][0],"sort":results[0][1],"href":results[0][2],"dalei":results[0][3]})

# 数据库: 此分类下公司爬取完上传is_used=1
def post_sort(id):
    # 链接数据库
    db = pymysql.connect(host="rm-bp1278x3bc1a6ujve1o.mysql.rds.aliyuncs.com", user="test_0527",passwd="test_0527",db="test_0527")
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 执行sql语句
    cursor.execute("UPDATE bfzyw_sort SET is_using = 1 WHERE id = {}".format(id))
    # 打印数据
    db.commit()
    cursor.close()  # 关闭连接

# 获取公司网址
def get_shop_html(shop_url):
    if re.search("^//",shop_url):shop_url = "http:" + shop_url
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        # 'Cookie': 'ASP.NET_SessionId=kzbhms11lkhh5xge0lzw2ly0; Hm_lvt_62c73c53c0ae8c986919225c11b0ff19=1591934094; __jsluid_h=2e43e5c8c22554578e4c4c462a2437c0; Hm_lpvt_62c73c53c0ae8c986919225c11b0ff19=1591945467',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
    }
    res = requests.get(shop_url+"/contact.aspx",headers=headers)
    # print(res.text)
    return res.text

# 爬取公司信息
def get_shop_info(html):
    soup = BeautifulSoup(html, 'lxml')
    固话 = ""
    phone = ""
    address = ""

    if "<h3>企业信息</h3>" in html:
        address = soup.select('span.sp')[0].string.lstrip()

        if len(soup.select('span.li02ok'))== 1:
            # 先找绑定手机的
            phone = re.search(r"\d+", soup.select('span.li02ok')[0].get('title'))[0]
        else:
            # 没有-就找底部的
            if len(soup.select('li.foot-contact>span>p:last-child')) == 1: phone = soup.select('li.foot-contact>span>p:last-child')[0].string
            phone = re.search("\d{11}", phone)[0] if re.search("\d{11}", phone) else ""

    elif "查看地图" in html:
        infos = soup.find_all("ul", attrs={"class": "gxrq"})
        for index, info in enumerate(infos):
            if "地址" in info.get_text(): address = info.get_text().replace("地址：", "").replace("查看地图", "")
            if "电话" in info.get_text(): 固话 = info.get_text().replace("电话：", "")
        # 手机
        infos = soup.find_all("dd", attrs={"class": ""})
        for index, info in enumerate(infos):
            # print(info)
            # 手机号
            if re.search("\d{11}", info.get_text()): phone = re.search("\d{11}", info.get_text())[0]

    elif "产品分类" or "联系方式" in html:
        if re.search("地　　址：(.+?)<", html): address = re.search("地　　址：(.+?)<", html)[1].lstrip()
        if re.search("电　　话：(.+?)<", html): phone = re.search("电　　话：(.+?)<", html)[1].lstrip()
        if re.search("手　　机：(.+?)<", html): 固话 = re.search("手　　机：(.+?)<", html)[1].lstrip()
    else:
        print("未知页面");sys.exit()

    return {'address': address, 'phone': phone, '固话': 固话}

# 公司数据:上传到数据库
def post_sjk(page, index, phone, 固话, shop_url, shop_name, address):
    payload = 'company_name=%s&trade=%s&address=%s&contact_name=%s&mobile=%s&phone=%s' % (shop_name, trade, address, lxr, phone, 固话)

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post("http://112.124.127.143:8049/api/CyShop/PostCyShopUserOne", headers=headers,
                             data=payload.encode("utf8"))
    print(response.text)
    # page:第几页/index:第几行
    print(page, index, phone, 固话, shop_url, shop_name, address)
    response = json.loads(response.text)

    if response["code"] != 0:
        print("上传错误")
        sys.exit()
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# 数据库: 获取分类数据
sort_info = get_sort()
trade = sort_info["sort"]
sort_href = sort_info["href"]

# 获取公司列表页_html
for page in range(1,200):
    url = 'https://www.b2b168.com{}l-{}.html'.format(sort_href,page)
    html = requests.get(url,headers=headers).text

    soup = BeautifulSoup(html,'lxml')

    for index,shop in enumerate(soup.find_all("div",attrs={"class": "biaoti"})):
        shop_url = shop.a.get('href')   #获取->公司网址
        # 获取->联系人名字
        lxr = shop.next_sibling.next_sibling.span.get_text().replace("(经理)","")
        # 特殊phone(在联系人中出现)
        lxr_phone = re.search("\d{11}", lxr)[0] if re.search("\d{11}",lxr) else ""
        # 获取->公司名
        shop_name = shop.a.get('title')

        # 获取->公司信息
        if shop_name == "八方资源网":pass
        else:
            # fun: 爬取公司信息
            shop_info = get_shop_info(get_shop_html(shop_url))
            address = shop_info["address"]
            固话    = shop_info["固话"]
            phone   = lxr_phone if shop_info["phone"] == "" else shop_info["phone"]

            if phone==""and 固话 == "":
                print(">>>>无联系方式: ",page,index,shop_url,shop_name+">>>>>>>>>>>>>>>>>>>>>>>>>>")
                # fun: 写入到文本
                write_to_txt(shop_url)
            else:
                # fun: 上传到数据库
                print(trade,sort_info["dalei"])
                post_sjk(page,index, phone, 固话, shop_url, shop_name, address)

    post_sort(sort_info["id"])





# print(phone,index,lxr,shop_url,shop_name,shop_info)

# # 测试
# if __name__ == '__main__':
#     url = 'http://fenqin888.b2b168.com/contact.aspx'
#     html = get_shop_info(url+"/contact.aspx")
#     # print(html)





'''
特殊页面: 
    http://m.fenqin888.b2b168.com
    https://www.b2b168.com/c168-5220579.html
    http://zq53297b2qnge.cn.b2b168.com/contact.aspx
'''