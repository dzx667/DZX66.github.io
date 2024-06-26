import os
import ctypes
import traceback
import sys
import datetime
import json
import base64
import shutil
from Crypto.Cipher import AES
from typing import Literal,Union

# str不是16的倍数那就补足为16的倍数
def add_to_16(message:str):
    while len(message) % 16 != 0:
        message = str(message)
        message += '\0'
    message = str(message)
    return message.encode('utf-8')  # 返回bytes


# 加密方法
def encrypt_oracle(message: str,key_pri: str):
    '''
    加密函数，传入明文 & 秘钥，返回密文；
    :param message: 明文
    :param key_pri: 秘钥
    :return:encrypted  密文
    '''
    # 初始化加密器
    aes = AES.new(add_to_16(key_pri), AES.MODE_ECB)
    # 将明文转为 bytes
    message_bytes = message.encode('utf-8')
    # 长度调整
    message_16 = add_to_16(message_bytes)
    #先进行aes加密
    encrypt_aes = aes.encrypt(message_16)
    #用base64转成字符串形式
    encrypt_aes_64 = base64.b64encode(encrypt_aes)
    return encrypt_aes_64.decode("utf-8")


# 解密方法
def decrypt_oralce(message,key_pri):
    '''
    解密函数，传入密文 & 秘钥，返回明文；
    :param message: 密文
    :param key_pri: 秘钥
    :return: encrypted 明文
    '''
    # 初始化加密器
    aes = AES.new(add_to_16(key_pri), AES.MODE_ECB)
    #优先逆向解密base64成bytes
    message_de64 = base64.b64decode(message)
    # 解密 aes
    message_de64_deaes = aes.decrypt(message_de64)
    message_de64_deaes_de = message_de64_deaes.decode('utf-8')
    message_de64_deaes_de = bytes(message_de64_deaes_de,'utf-8').decode('unicode_escape').encode('latin1').decode()
    message_de64_deaes_de = message_de64_deaes_de.replace("\x00","")[2:-1]
    return message_de64_deaes_de


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def update_index(is_show_all:bool=True):
    '''更新页面索引 
    @is_show_all: 是否显示读取到的页面'''
    print("正在更新页面索引...")
    res = {}
    for dir in os.listdir("pages"):
        with open(os.path.join("pages",dir,"attribute.json"),"r",encoding="utf-8") as f:
            datar = json.load(f)
        if is_show_all:
            print("标题：{0}\t是否上锁：{1}\t标签：{2}".format(datar["title"],str(datar["is_locked"]),str(datar["tags"])))
        res[datar["title"]] = datar
    datar = json.dumps(res, sort_keys=True, indent=4, separators=(',', ': '),ensure_ascii=False)
    with open("index.json","w",encoding="utf-8") as f:
        f.write(datar)
    print("完成 共"+str(len(res))+"个项目")

def edit_page():
    '''操作页面'''
    
    while True:
        update_index(False)
        with open("index.json","r",encoding="utf-8") as f:
            data:dict[str,dict[Literal["title","tags","is_locked","create_time","last_edit_time"],Union[str,bool,list[str]]]] = json.load(f)
        
        m = 0
        ordered_data:dict[int,dict[Literal["title","tags","is_locked","create_time","last_edit_time"],Union[str,bool,list[str]]]] = {}
        for i in data:
            m += 1
            ordered_data[m] = data[i]
        print("="*5)
        for i in ordered_data:
            print(str(i) + "\t" + ordered_data[i]["title"] + "\t" + ordered_data[i]["last_edit_time"])
        print("="*5)
        cmd = ""
        while True:
            cmd = input("选择一项（按0撤回）：")
            try:
                cmd = int(cmd)
                if cmd == 0:
                    return -1
                elif cmd < 0 or cmd > m:
                    raise ValueError
                else:
                    break
            except ValueError:
                print("输入不符合要求")
        title = ordered_data[cmd]["title"]
        dir = os.path.join("pages",title)
        is_locked = ordered_data[cmd]["is_locked"]
        tags = ordered_data[cmd]["tags"]
        create_time = ordered_data[cmd]["create_time"]
        latest_edit_time = ordered_data[cmd]["last_edit_time"]
        print()
        while True:
            print()
            print("当前位置：页面管理 -> " + title)
            print("目标路径：" + dir)
            print("标题：" + title)
            print("是否上锁：" + ("是" if is_locked else "否"))
            print("创建时间：" + create_time)
            print("最后一次修改时间：" + latest_edit_time)
            o = ""
            for i in tags:
                o += i+" "
            print("标签：" + o)
            print("="*10)
            print("0.返回上一级")
            print("1.修改标题")
            print("2.上锁/解锁")
            print("3.修改标签")
            print("4.修改内容")
            print("5.查看内容")
            print("6.删除页面")
            print("="*10)
            cmd = input("输入指令：")
            print()
            if cmd == "0":
                break
            elif cmd == "1":
                ntitle = ""
                while ntitle == "":
                    ntitle = input("新标题：")
                    ndir = os.path.join("pages",ntitle)
                    if ntitle == "":
                        print("不能为空！")
                    if os.path.exists(ndir):
                        print("该页面已存在！")
                        ntitle = ""
                os.mkdir(ndir)
                shutil.copyfile(os.path.join(dir,"content.html"),os.path.join(ndir,"content.html"))
                shutil.copyfile(os.path.join(dir,"attribute.json"),os.path.join(ndir,"attribute.json"))
                with open(os.path.join(ndir,"attribute.json"),"r",encoding="utf-8") as f:
                    attributes:dict[Literal["title","tags","is_locked","create_time","last_edit_time"],Union[str,bool,list[str]]] = json.load(f)
                attributes["title"] = ntitle
                datar = json.dumps(attributes, sort_keys=True, indent=4, separators=(',', ': '),ensure_ascii=False)
                with open(os.path.join(ndir,"attribute.json"),"w",encoding="utf-8") as f:
                    f.write(datar)
                os.remove(os.path.join(dir,"content.html"))
                os.remove(os.path.join(dir,"attribute.json"))
                os.remove(dir)
                title = ntitle
                dir = ndir
            elif cmd == "2":
                with open(os.path.join(dir,"content.html"),"r",encoding="utf-8") as f:
                    org_content = f.read()
                if is_locked:
                    while True:
                        password = input("请输入密码：")
                        try:
                            content = decrypt_oralce(org_content,password)
                            if content[:6] != "locked":
                                raise ValueError
                        except Exception:
                            print("密码错误")
                        else:
                            content = content[6:]
                            break
                    with open(os.path.join(dir,"content.html"),"w",encoding="utf-8") as f:
                        f.write(content)
                    with open(os.path.join(dir,"attribute.json"),"r",encoding="utf-8") as f:
                        attributes:dict[Literal["title","tags","is_locked","create_time","last_edit_time"],Union[str,bool,list[str]]] = json.load(f)
                    attributes["is_locked"] = False
                    datar = json.dumps(attributes, sort_keys=True, indent=4, separators=(',', ': '),ensure_ascii=False)
                    with open(os.path.join(dir,"attribute.json"),"w",encoding="utf-8") as f:
                        f.write(datar)
                    is_locked = False
                else:
                    password = ""
                    while password == "":
                        password = input("设置密码：")
                        if password == "":
                            print("不能为空！")
                    r = encrypt_oracle("locked"+org_content,password)
                    with open(os.path.join(dir,"content.html"),"w",encoding="utf-8") as f:
                        f.write(r)
                    with open(os.path.join(dir,"attribute.json"),"r",encoding="utf-8") as f:
                        attributes:dict[Literal["title","tags","is_locked","create_time","last_edit_time"],Union[str,bool,list[str]]] = json.load(f)
                    attributes["is_locked"] = True
                    datar = json.dumps(attributes, sort_keys=True, indent=4, separators=(',', ': '),ensure_ascii=False)
                    with open(os.path.join(dir,"attribute.json"),"w",encoding="utf-8") as f:
                        f.write(datar)
                    is_locked = True
            elif cmd == "4":
                with open(os.path.join("pages",title,"content.html"),"r",encoding="utf-8") as f:
                    org_content = f.read()
                with open(os.path.join("pages",title,"attribute.json"),"r",encoding="utf-8") as f:
                    attributes:dict[Literal["title","tags","is_locked","create_time","last_edit_time"],Union[str,bool,list[str]]] = json.load(f)
                if attributes["is_locked"]:
                    while True:
                        password = input("请输入密码：")
                        try:
                            content = decrypt_oralce(org_content,password)
                            if content[:6] != "locked":
                                raise ValueError
                        except Exception:
                            print("密码错误")
                        else:
                            content = content[6:]
                            break
                else:
                    content = org_content
                f = open("temp.html","w",encoding="utf-8")
                f.write('<!DOCTYPE html><html lang="zh-CN"><head><title>{title}</title><link rel="stylesheet" type="text/css" href="../style.css"><script src="../template.js"></script><meta name="viewport" content="width=device-width, initial-scale=1"><meta charset="utf-8"></head><body><h1>{title}</h1><p>最后一次更新时间：{date}</p><p>创建时间：{create}</p><hr>\n<!-- 请在以下写入代码 -->\n{content}\n<!-- 请在以上写入代码 -->\n<script>refresh();</script>'.format(title=title,date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),content=content,create=attributes["create_time"]))
                f.close()
                os.system('start "" "D:/Microsoft VS Code/Code.exe" temp.html')
                print("请修改后保存")
                os.system("pause")
                f = open("temp.html","r",encoding="utf-8")
                res = f.readlines()[2:-2]
                f.close()
                os.remove("temp.html")
                r = ""
                for i in res:
                    r += i
                r = r[:-1]
                if is_locked:
                    r = encrypt_oracle("locked"+r,password)
                with open(os.path.join("pages",title,"content.html"),"w",encoding="utf-8") as f:
                    f.write(r)
                datar = json.dumps({"title":title,"tags":attributes["tags"],"is_locked":attributes["is_locked"],"create_time":attributes["create_time"],"last_edit_time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, sort_keys=True, indent=4, separators=(',', ': '),ensure_ascii=False)
                with open(os.path.join("pages",title,"attribute.json"),"w",encoding="utf-8") as f:
                    f.write(datar)
            elif cmd == "5":
                with open(os.path.join("pages",title,"content.html"),"r",encoding="utf-8") as f:
                    org_content = f.read()
                with open(os.path.join("pages",title,"attribute.json"),"r",encoding="utf-8") as f:
                    attributes:dict[Literal["title","tags","is_locked","create_time","last_edit_time"],Union[str,bool,list[str]]] = json.load(f)
                if attributes["is_locked"]:
                    while True:
                        password = input("请输入密码：")
                        try:
                            content = decrypt_oralce(org_content,password)
                            if content[:6] != "locked":
                                raise ValueError
                        except Exception:
                            print("密码错误")
                        else:
                            content = content[6:]
                            break
                else:
                    content = org_content
                f = open("temp.html","w",encoding="utf-8")
                f.write('<!DOCTYPE html><html lang="zh-CN"><head><title>{title}</title><link rel="stylesheet" type="text/css" href="../style.css"><script src="../template.js"></script><meta name="viewport" content="width=device-width, initial-scale=1"><meta charset="utf-8"></head><body><h1>{title}</h1><p>最后一次更新时间：{date}</p><p>创建时间：{create}</p><hr>\n<!-- 请在以下写入代码 -->\n{content}\n<!-- 请在以上写入代码 -->\n<script>refresh();</script>'.format(title=title,date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),content=content,create=attributes["create_time"]))
                f.close()
                os.system('start temp.html')
                os.system("pause")
                os.remove("temp.html")
            elif cmd == "6":
                while True:
                    confirm = input("确定要删除吗，此操作不可逆（本地）！(y/n)：")
                    if confirm == "y":
                        confirm = True
                        break
                    elif confirm == "n":
                        confirm = False
                        break
                if confirm:
                    shutil.rmtree(dir)
                    break
def new_page():
    '''新建页面'''
    title = ""
    while title == "":
        title = input("标题（按0撤回）：")
        if title == "0":
            return -1
        dir = os.path.join("pages",title)
        if title == "":
            print("不能为空！")
        if os.path.exists(dir):
            print("该页面已存在！")
            title = ""
    tags = []
    while True:
        tag = input("标签（按0结束）：")
        if tag == "0":
            break
        else:
            if tag == "" or tag == " ":
                print("不能为空")
            else:
                tags.append(tag)
    while True:
        locked = input("是否上锁(y/n)：")
        if locked == "y":
            locked = True
            password = ""
            while password == "":
                password = input("密码：")
                if password == "":
                    print("不能为空！")
            break
        elif locked == "n":
            locked = False
            break
    f = open("temp.html","w",encoding="utf-8")
    f.write('<!DOCTYPE html><html lang="zh-CN"><head><title>{title}</title><link rel="stylesheet" type="text/css" href="../style.css"><script src="../template.js"></script><meta name="viewport" content="width=device-width, initial-scale=1"><meta charset="utf-8"></head><body><h1>{title}</h1><p>最后一次更新时间：{date}</p><p>创建时间：{date}</p><hr>\n<!-- 请在以下写入代码 -->\n\n<!-- 请在以上写入代码 -->\n<script>refresh();</script>'.format(title=title,date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    f.close()
    os.system('start "" "D:/Microsoft VS Code/Code.exe" temp.html')
    print("请修改后保存")
    os.system("pause")
    f = open("temp.html","r",encoding="utf-8")
    res = f.readlines()[2:-2]
    f.close()
    os.remove("temp.html")
    r = ""
    for i in res:
        r += i
    os.mkdir(dir)
    if locked:
        r = encrypt_oracle("locked"+r,password)
    with open(os.path.join(dir,"content.html"),"w",encoding="utf-8") as f:
        f.write(r)
    datar = json.dumps({"title":title,"tags":tags,"is_locked":locked,"create_time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"last_edit_time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, sort_keys=True, indent=4, separators=(',', ': '),ensure_ascii=False)
    with open(os.path.join(dir,"attribute.json"),"w",encoding="utf-8") as f:
        f.write(datar)

def apply():
    '''部署网站'''
    update_index(False)
    # 删除原有文件
    print("删除原有文件...")
    folder_path = "../pages"
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
    print("创建文件...")
    # 创建文件
    with open("index.json","r",encoding="utf-8") as f:
        data:dict[str,dict[Literal["title","tags","is_locked","create_time","last_edit_time"],Union[str,bool,list[str]]]] = json.load(f)
    for i in data:
        with open(os.path.join("../pages/",data[i]["title"]+".html"),"w",encoding="utf-8") as f:
            if data[i]["is_locked"]:
                with open(os.path.join("pages",data[i]["title"],"content.html"),"r",encoding="utf-8") as f1:
                    f.write(r'<!DOCTYPE html><html lang="zh-CN"><head><title>{title} - 柳下回声</title><link rel="stylesheet" type="text/css" href="../style.css"><meta name="viewport" content="width=device-width, initial-scale=1"><meta charset="utf-8"><meta name="referrer" content="no-referrer"><script src="../system/crypto-js.min.js"></script><script src="../template.js"></script></head><body><h1>{title}</h1><a href="../blogs.html">返回</a><p>最后一次更新时间：{date}</p><p>创建时间：{create}</p><hr><div id="tip"><p>这个文档被加密了，需要密码...</p><br/><span>密码：</span><input type="password" name="password" id="2"><button onclick="sure();">确定</button></div><div id="1"></div><script>document.getElementById("2").addEventListener("keydown",function(event){{if(event.key === "Enter"){{sure();event.preventDefault();}}}});function sure(){{var akey=document.getElementById("2").value;while(akey.length%16!=0){{akey+="\0"}};var key=CryptoJS.enc.Utf8.parse(akey);const mode=CryptoJS.mode.ECB;const padding=CryptoJS.pad.Pkcs7;var decryptedText=CryptoJS.AES.decrypt("{base64}",key,{{mode,padding}});var a=decodeURIComponent(CryptoJS.enc.Utf8.stringify(decryptedText).replace(/\\x/g,"%"));document.getElementById("1").innerHTML=a;if(document.getElementById("1").innerHTML.slice(2,8)=="locked"){{document.getElementById("tip").innerHTML="";}}document.getElementById("1").innerHTML=document.getElementById("1").innerHTML.replace(/\\n/g,"").slice(8,-1);refresh();}}</script></body></html>'.format(title=data[i]["title"],date=data[i]["last_edit_time"],create=data[i]["create_time"],base64=f1.read()))
            else:
                f.write('<!DOCTYPE html><html lang="zh-CN"><head><title>{title} - 柳下回声</title><link rel="stylesheet" type="text/css" href="../style.css"><script src="../template.js"></script><meta name="viewport" content="width=device-width, initial-scale=1"><meta charset="utf-8"><meta name="referrer" content="no-referrer"></head><body><h1>{title}</h1><a href="../blogs.html">返回</a><p>最后一次更新时间：{date}</p><p>创建时间：{create}</p><hr>\n'.format(title=data[i]["title"],date=data[i]["last_edit_time"],create=data[i]["create_time"]))
                with open(os.path.join("pages",data[i]["title"],"content.html"),"r",encoding="utf-8") as f1:
                    f.write(f1.read())
                f.write('</body><script>refresh();</script></html>')
    # 创建索引
    print("创建索引...")
    with open("../blogs.html","w",encoding="utf-8") as f:
        f.write('<!DOCTYPE html><html lang="zh-CN"><head><title>柳下回声</title><link rel="stylesheet" type="text/css" href="style.css"><meta name="viewport" content="width=device-width, initial-scale=1"><meta charset="utf-8"></head><body><h1>柳下回声</h1><p>最后一次更新时间：{date}</p><hr><ul style="list-style-type: none;">'.format(date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        for i in data:
            tag = ""
            for o in data[i]["tags"]:
                tag+=o+" "
            f.write("<li><div class='head'><a href='pages/{title}.html'>{title}</a></div><div class='foot'> {locked} 更新时间：{date} 标签：{tags}</div></li>".format(title=data[i]["title"],locked="已加密" if data[i]["is_locked"] else "公开",date=data[i]["last_edit_time"],tags=tag))
        f.write("</ul></body></html>")
    print("完成")
if __name__=="__main__":
    if is_admin():
        try:
            print(__file__)
            if "Temp" not in __file__:
                os.chdir(os.path.dirname(os.path.abspath(__file__)))
            while True:
                print()
                cmd = None
                print("工作目录：",os.getcwd())
                print("="*10)
                print("这是网站后台")
                print("1.页面管理")
                print("2.网站部署")
                print("="*10)
                cmd = input("输入指令：")
                print()
                if cmd == "1":
                    while True:
                        print()
                        print("当前位置：页面管理")
                        print("="*10)
                        print("0.返回上一级")
                        print("1.操作已有页面")
                        print("2.更新页面索引")
                        print("3.创建页面")
                        print("="*10)
                        cmd = input("输入指令：")
                        print()
                        if cmd == "0":
                            break
                        elif cmd == "1":
                            edit_page()
                        elif cmd == "2":
                            update_index()
                        elif cmd == "3":
                            new_page()
                elif cmd == "2":
                    apply()
        except Exception as e:
            traceback.print_exc()
            input()
    else:
        ctypes.windll.shell32.ShellExecuteW(None,"runas",sys.executable,__file__,None,1)