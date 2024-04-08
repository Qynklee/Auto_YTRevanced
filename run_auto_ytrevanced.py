import os
import subprocess
import html
import requests
import json
import time
import sys
from apkmirror import APKMirror
import telebot
import random

BOT_TOKEN = '123456789:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
CHANNEL_ID = -100123456789
TELE_BOT = telebot.TeleBot(BOT_TOKEN)


YT_STOCK_FILE = "youtube_stock.apk"
PATCHES_JAR_FILE = "revanced_patches.jar"
REVANCED_CLI_FILE = "revanced_cli.jar"
REVANCED_INTEGRITY_FILE = "revanced_integrity.apk"
OPTIONS_JSON_FILE = "options.json"
OPTIONS_JSON_PKGNAME_FILE = "options_change_pkgname.json"

YT_REVANCED_FILE = "youtube_revanced_patched.apk"
YT_REVANCED_FAKE_PKG_FILE = "youtube_revanced_patched_fakename.apk"

apkm = APKMirror(timeout=3, results=5)

def check_yt_version():
    lastest_patches = "https://api.github.com/repos/ReVanced/revanced-patches/releases/latest"
    resp = requests.get(lastest_patches)

    if(resp.status_code == 200):
        patches_json_url = ""
        data = resp.json()

        all_item_list = data['assets']
        for item in all_item_list:
            if(item['name'] == 'patches.json'):
                patches_json_url = item["browser_download_url"]
                break

        if(patches_json_url != ""):
            print(patches_json_url)
            resp2 = requests.get(patches_json_url)
            if(resp2.status_code == 200):
                patches_json = resp2.json()
                for patch in patches_json:
                    if( patch["compatiblePackages"][0]["name"] == "com.google.android.youtube"):
                        newest_yt_version = patch["compatiblePackages"][0]["versions"][-1]
                        return newest_yt_version

    return ""

def download_yt_apk(yt_version: str):
    numver = yt_version.split(".")
    yt_page_url = "https://www.apkmirror.com/apk/google-inc/youtube/youtube-"+numver[0]+"-"+numver[1]+"-"+numver[2]+"-release/"
    print("Page link: ", yt_page_url)
    app_details = apkm.get_app_details(yt_page_url)
    app_link = app_details["download_link"]
    print("applink", app_link)
    print("app_details:", app_details)
    direct_link = apkm.get_download_link(app_link)
    print("Got direct download link! Remove old file and download...")

    if os.path.exists(YT_STOCK_FILE):
        os.remove(YT_STOCK_FILE)

    apkm.download_file_by_directlink(apkm.get_direct_download_link(direct_link), YT_STOCK_FILE)

    return


def download_revanced_dependencies():

    #Revanced patches.jar
    lastest_patches = "https://api.github.com/repos/ReVanced/revanced-patches/releases/latest"
    resp = requests.get(lastest_patches)

    if(resp.status_code == 200):
        patches_jar_url = ""
        data = resp.json()

        all_item_list = data['assets']
        for item in all_item_list:
            if(str(item['name']).endswith(".jar")):
                patches_jar_url = item["browser_download_url"]
                break

        if(patches_jar_url != ""):
            resp2 = requests.get(patches_jar_url, allow_redirects=True)
            if(resp2.status_code == 200):
                patches_jar_data = resp2.content
                with open(PATCHES_JAR_FILE, "wb") as fo1:
                    fo1.write(patches_jar_data)

    #Revanced cli.jar
    lastest_cli = "https://api.github.com/repos/ReVanced/revanced-cli/releases/latest"
    resp = requests.get(lastest_cli)

    if(resp.status_code == 200):
        revanced_cli_url = ""
        data = resp.json()

        all_item_list = data['assets']
        for item in all_item_list:
            if(str(item['name']).endswith(".jar")):
                revanced_cli_url = item["browser_download_url"]
                break

        if(revanced_cli_url != ""):
            resp2 = requests.get(revanced_cli_url, allow_redirects=True)
            if(resp2.status_code == 200):
                revanced_cli_data = resp2.content
                with open(REVANCED_CLI_FILE, "wb") as fo1:
                    fo1.write(revanced_cli_data)


    #Revanced intergrity.jar
    lastest_integrity = "https://api.github.com/repos/revanced/revanced-integrations/releases/latest"
    resp = requests.get(lastest_integrity)

    if(resp.status_code == 200):
        revanced_integrity_url = ""
        data = resp.json()

        all_item_list = data['assets']
        for item in all_item_list:
            if(str(item['name']).endswith(".apk")):
                revanced_integrity_url = item["browser_download_url"]
                break

        if(revanced_integrity_url != ""):
            resp2 = requests.get(revanced_integrity_url, allow_redirects=True)
            if(resp2.status_code == 200):
                revanced_integrity_data = resp2.content
                with open(REVANCED_INTEGRITY_FILE, "wb") as fo1:
                    fo1.write(revanced_integrity_data)

    return


def create_options_json_file():
    if os.path.exists(OPTIONS_JSON_FILE):
        os.remove(OPTIONS_JSON_FILE)


    create_options_1 = subprocess.run(["java", "-jar", REVANCED_CLI_FILE, "options", "-o", PATCHES_JAR_FILE])
    print("Create stock options.json was: %d" % create_options_1.returncode)

    if os.path.exists(OPTIONS_JSON_FILE):
        fop = open(OPTIONS_JSON_FILE, "r")
        options_json = json.load(fop)
        new_data = {"patchName" : "Change package name","options" : [ {
            "key" : "packageName",
            "value" : "com.google.android.youtube"} ]}
        
        new_options_json = []

        for item in options_json:
            if(item["patchName"] == "Change package name"):
                # item["options"]["value"] = "com.google.android.youtube"
                new_options_json.append(new_data)
            else:
                new_options_json.append(item)
                

        #write package name stock options json file:
        if os.path.exists(OPTIONS_JSON_PKGNAME_FILE):
            os.remove(OPTIONS_JSON_PKGNAME_FILE)

        foo = open(OPTIONS_JSON_PKGNAME_FILE, "w")
        json.dump(new_options_json,foo)
        foo.close()
        fop.close()

    return

def run_patching():

    if(os.path.exists(YT_REVANCED_FILE)):
        os.remove(YT_REVANCED_FILE)
    #patching apk with revanced package name:
    try:
        revanced_patch = subprocess.run(["java", "-Xmx2048m", "-jar", REVANCED_CLI_FILE, "patch", "--options="+OPTIONS_JSON_FILE, "-b" ,PATCHES_JAR_FILE, "-m", REVANCED_INTEGRITY_FILE, "-o", YT_REVANCED_FILE, YT_STOCK_FILE])
        print("The exit code was: %d" % revanced_patch.returncode)
    except Exception as e:
        if(os.path.exists(YT_REVANCED_FILE)):
            os.remove(YT_REVANCED_FILE)

    if(os.path.exists(YT_REVANCED_FAKE_PKG_FILE)):
        os.remove(YT_REVANCED_FAKE_PKG_FILE)

    try:
        revanced_patch = subprocess.run(["java", "-Xmx2048m", "-jar", REVANCED_CLI_FILE, "patch", "--options="+OPTIONS_JSON_PKGNAME_FILE, "-b" ,PATCHES_JAR_FILE, "-m", REVANCED_INTEGRITY_FILE, "-o", YT_REVANCED_FAKE_PKG_FILE, YT_STOCK_FILE])
        print("The exit code was: %d" % revanced_patch.returncode)
    except Exception as e:
        if(os.path.exists(YT_REVANCED_FAKE_PKG_FILE)):
            os.remove(YT_REVANCED_FAKE_PKG_FILE)

    return


def create_tele_message(yt_version: str):
    message_head = TELE_BOT.send_message(CHANNEL_ID, "New ZiuTub Revanced version: " + yt_version + " is updated!!")

    ### move data to share folder.

    return


def run_http_server():
    new_port = random.randint(10000, 20000)
    
    return

def cleanup_after_patching():

    #delete temp folder:
    os.system('rm -rf *-temporary-files')
    os.system('rm -rf *.keystone')

    return


def main():
    try:
        f1 = open("yt_lastest_ver.txt", "r")
        yt_version = f1.read().replace("\n", "").replace("\r", "")
        f1.close()
    except:
        yt_version = ""

    if(yt_version == None):
        yt_version = ""

    while(True):
        newest_yt_version = check_yt_version()

        if(newest_yt_version == ""):
            print("newest_yt_version: --\n Sleep 12hours" )
            time.sleep(43200)
            continue
        elif(newest_yt_version != yt_version):
            #create new version:
            yt_version = newest_yt_version
            with open("yt_lastest_ver.txt", "w") as f2:
                f2.write(yt_version)

            download_yt_apk(yt_version)

            download_revanced_dependencies()
            create_options_json_file()
            run_patching()
            create_tele_message(yt_version)
            if(sys.platform == 'linux'):
                cleanup_after_patching()

            #sleep
            time.sleep(43200)
        else:
            time.sleep(43200)
    return

main()


# def test():
#     for i in ["java", "-jar", REVANCED_CLI_FILE, "patch", "--options="+OPTIONS_JSON_PKGNAME_FILE, "-b" ,PATCHES_JAR_FILE, "-m", REVANCED_INTEGRITY_FILE, "-o", YT_REVANCED_FAKE_PKG_FILE, YT_STOCK_FILE]:
#         print(i, end=" ")

#     return

# test()