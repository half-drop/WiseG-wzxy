# _*_ coding: utf-8 _*_
"""
Time:     2023/2/12 16:21
Author:   Dominic
File:     jkdj_v4.3_email_ding.py
Describe: 
"""

''' 必填项 '''
account = ""  # 通常是手机号
password = ""  # 密码
province = ""  # 省
city = ""  # 市
district = ""  # 县
street = ""  # 街
town = ""  # 街道
signArea = ""  # 学校，校外不填

''' 邮箱提醒（可选） '''
mySender = ""  # 发件人邮箱
myToken = ""  # 发件人邮箱授权码
myReceiver = ""  # 收件人邮箱，可以和发件人邮箱相同

''' 钉钉提醒（可选） '''
mySecret = ''  # 钉钉密钥
myWebhook = ''  # 钉钉webhook

''' 代码 '''
import base64
import hashlib
import hmac
import json
import random
import smtplib
import time
import urllib.parse
import urllib.request
import requests
from email.mime.text import MIMEText
from email.utils import formataddr
from func_timeout import FunctionTimedOut, func_timeout

session = requests.session()


# 登录
def login():
    login_url = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username?"
    print("〇 登录…… ")
    url = login_url + "username=" + account + "&password=" + password
    session.headers['Referer'] = "https://gw.wozaixiaoyuan.com/h5/mobile/basicinfo/index/login/index"
    resp = session.post(url, data="{}")
    res = json.loads(resp.text)
    res['status'] = -10000
    if res["code"] == 0:
        print("√ 登录成功。")
        session.headers['JWSESSION'] = resp.headers['JWSESSION']
        w_session(session.headers)
        check_jkdk()
    elif res['code'] == 101:
        print("× 密码异常，请修改！")
        print("× Error: ", res['message'])
        res['status'] = 10001
        observer(res)
        change_pwd()
    else:
        print("× 登录异常！")
        print("× Error: ", res['message'])
        res['status'] = 10002
        observer(res)
    return res


# 修改密码
def change_pwd():
    ch_pwd_api = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/changePassword?"
    get_code_url = 'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/getCode?phone=' + account
    session.get(get_code_url)
    code = ''
    try:
        code = func_timeout(60, lambda: input('〇 输入验证码：'))
        print('code:', code)
    except FunctionTimedOut:
        print("超时了哦~")
        res = {'status': 10003}
        observer(res)
        return
    ch_pwd_url = ch_pwd_api + 'phone=' + account + '&code=' + code + '&password=' + password
    session.headers['Referer'] = "https://gw.wozaixiaoyuan.com/h5/mobile/basicinfo/index/login/changePassword"
    res = session.get(ch_pwd_url).json()
    print(res)
    if res['code'] == 0:
        print("√ 修改成功，尝试重新登录……")
        login()
    else:
        print("× 修改密码失败！")
        print("× Error: ", res['message'])
        res['status'] = 10004
        observer(res)
    return res


# 打卡
def check_jkdk():
    jkdk_api = "https://gw.wozaixiaoyuan.com/health/mobile/health/save?batch="
    batchId = getBatch()
    url = jkdk_api + batchId
    if signArea is "":
        data1 = {
            'locationType': 0,
            'inSchool': 0,
            'location': "中国/" + province + "/" + city + "/" + district + "/" + street
        }
    else:
        data1 = {
            'locationType': 1,
            'inSchool': 1,
            'location': 0,
            'signArea': signArea
        }
    data2 = {
        "t1": "[\"无特殊情况，身体健康；\"]",
        "t2": get_random_temperature(),
        "locationState": -1,  # 位置异动：-1正常 0待确认 1异常
        "type": 0,  # 异常状态：0正常 1异常
    }
    data = json.dumps(dict(data1, **data2))
    session.headers['Referer'] = 'https://gw.wozaixiaoyuan.com/h5/mobile/health/0.1.6/health/detail?id=' + batchId
    res = session.post(url, data=data).json()
    res['status'] = -1
    if res['code'] is 103:
        print('× 打卡失败！')
        print('× Error: 未登录，即将登录。')
        login()
        check_jkdk()
    if res['code'] == 0:
        print("√ 打卡成功.")
        res['status'] = 0
        observer(res)
    else:
        print("× 打卡失败！")
        print("× Error: ", res['message'])
        res['status'] = res['code']
        observer(res)
    return res


# 获取打卡id
def getBatch():
    url = 'https://gw.wozaixiaoyuan.com/health/mobile/health/getBatch'
    session.headers['Referer'] = 'https://gw.wozaixiaoyuan.com/h5/mobile/health/0.1.8/health'
    res = session.post(url).json()
    if res['code'] is 103:
        print('× 获取打卡id失败！')
        print('× Error: 未登录，即将登录。')
        login()
        exit(0)
    batchId = res['data']['list'][0]['id']
    return batchId


# 随机体温
def get_random_temperature():
    random.seed(time.ctime())
    return "{:.1f}".format(random.uniform(36.2, 36.7))


# 保存登录态
def w_session(s):
    s = json.dumps(s, sort_keys=False, indent=4, separators=(',', ': '))
    f = open('session.json', 'w')
    f.write(str(s))


# 读取登录态
def r_session():
    try:
        f = open('session.json', 'r')
    except Exception as e:
        return
    s = json.load(f)
    return s


# 状态
def get_status(status):
    if status == 10001:
        return "× 密码异常，将执行修改程序，请前往控制台输入验证码！"
    elif status == 10002:
        return "× 登录异常！"
    elif status == 10003:
        return "× 密码输入超时！"
    elif status == 10004:
        return "× 密码修改失败！"
    elif status == 0:
        return "健康打卡成功~"
    elif status == 1:
        return "〇 打卡时间已过"
    elif status == -10:
        return "× 无法登录"
    else:
        return "× 未知异常"


# 发送提醒
def observer(res):
    status = res['status']
    msg=''
    if 'message' in res.keys():
        msg='\n\n服务器消息\n'+res['message']
    if mySender and myToken and myReceiver:
        print('√ 执行邮件提醒')
        send_email(status,msg)
    else:
        print('× 未启用邮件提醒')
    if myWebhook and mySecret:
        print('√ 执行钉钉提醒')
        send_ding(status,msg)
    else:
        print('× 未启用钉钉提醒')


# 发送邮件
def send_email(status,s_msg):
    try:
        msg = MIMEText("Wise_G已经帮你完成【我在校园健康打卡】了喔>_<，" + get_status(status)+s_msg, 'plain', 'utf-8')
        msg['From'] = formataddr(["Wise_G打卡服务", mySender])  # 双引号内是发件人昵称，可以自定义
        msg['To'] = formataddr(["half_drop", myReceiver])  # 双引号内是收件人邮箱昵称，可以自定义
        msg['Subject'] = get_status(status)
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(mySender, myToken)
        server.sendmail(mySender, [myReceiver, ], msg.as_string())
        server.quit()  # 关闭邮箱连接
        print("√ 邮件发送成功。")
        status = True
    except Exception as e:
        print("× 邮件发送失败！")
        print("× Error: ", e)


# 发送钉钉
def send_ding(status,s_msg):
    url = myWebhook
    secret = mySecret
    timestamp = round(time.time() * 1000)  # 时间戳
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))  # 最终签名
    webhook_url = url + '&timestamp={}&sign={}'.format(timestamp, sign)  # 最终url，url+时间戳+签名
    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    send_data = {
        "msgtype": "text",
        "text": {
            "content": "Wise_G已经帮你完成【我在校园健康打卡】了喔 >_<"
        }
    }
    if status is not 0:
        send_data["at"] = {
            "atMobiles": [account],
            "isAtAll": False
        }
    send_data = json.dumps(send_data)  # 将字典类型数据转化为json格式
    send_data = send_data.encode("utf-8")  # 编码为UTF-8格式
    res = urllib.request.Request(url=webhook_url, data=send_data, headers=header)  # 发送请求
    res = urllib.request.urlopen(res).read()  # 将请求发回的数据构建成为文本格式
    res = eval(str(res, 'utf-8'))
    if res['errcode'] is 0:
        print('√ 发送钉钉提醒成功。')
    else:
        print('× 发送钉钉提醒失败！')


# 主函数
def run():
    session.headers = {
        "Host": "gw.wozaixiaoyuan.com",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Keep-Alive": "timeout=60",
        "User_Agent": "User-Agent: Mozilla/5.0 (Linux; Android 11; V2055A Build/RP1A.200720.012; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4277 MMWEBSDK/20220706 Mobile Safari/537.36 MMWEBID/815 MicroMessenger/8.0.25.2200(0x2800193B) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91",
    }
    s = r_session()
    if s:
        session.headers = s
    checkRes = {'status': False}
    checkRes = check_jkdk()
    res = {'@Author ': 'Dominic&Smallway'}
    if checkRes['status'] != 0:
        res['Check Exception'] = 'Please read the console log.'
    return res


if __name__ == '__main__':
    run()


def handler(event, context):
    return run()
