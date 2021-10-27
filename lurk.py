import os
import sys
import time
import asyncio
import base64
import hashlib
import uuid

import requests

apiurl = "https://api.ifunny.mobi"
basicauth = None
bearerauth = None
hasPrimed = False
primtime = 0


async def genAndPrimBasic():
    clientid = "MsOIJ39Q28"
    clientsecret = "PTDc3H8a)Vi=UYap"

    hexstring = str(uuid.uuid4()).encode("utf-8").hex().upper()
    hexid = hexstring + "_" + clientid
    hash_decoded = hexstring + ":" + clientid + ":" + clientsecret
    hash_encoded = hashlib.sha1(hash_decoded.encode("utf-8")).hexdigest()
    bauth = base64.b64encode(bytes(hexid + ":" + hash_encoded, "utf-8")).decode()

    primurl = apiurl + "/v4/counters"
    daheader = {"Authorization": "Basic " + bauth,
                "Ifunny-Project-Id": "iFunny",
                "User-Agent": "iFunny/7.6.1(21916) iphone/15.1 (Apple; iPhone12,3)"}
    res = requests.get(url=primurl, headers=daheader)
    if res.status_code == 200:
        global primtime
        primtime = int(round(time.time() * 1000))
        global hasPrimed
        hasPrimed = True

    global basicauth
    basicauth = bauth

    prim_path = "primed_basic.txt"
    with open(prim_path, "w+") as bf:
        bf.write(bauth)


async def byNick():
    if bearerauth is not None:
        lurkee = input("Type username of the person you want to indefinitely lurk on: ")
        bynickurl = apiurl + "/v4/users/by_nick/" + lurkee
        nickheader = {"Authorization": "Bearer " + bearerauth,
                      "Ifunny-Project-Id": "iFunny",
                      "User-Agent": "iFunny/7.6.1(21916) iphone/15.1 (Apple; iPhone12,3)"}

        nick_res = requests.get(url=bynickurl, headers=nickheader)

        return nick_res


async def lurk():
    if bearerauth is not None:
        nick_res = await byNick()

        while nick_res.status_code != 200:
            print("No user with that name was found. Plz try again")
            print(nick_res.json())
            nick_res = await byNick()

        print("Lurking... (Type CTRL+C or click stop button to stop)")
        while True:
            udata = nick_res.json()
            uid = udata["data"]["id"]
            lurkurl = apiurl + "/v4/users/" + uid
            lurkheader = {"Authorization": "Bearer " + bearerauth,
                          "Ifunny-Project-Id": "iFunny",
                          "User-Agent": "iFunny/7.6.1(21916) iphone/15.1 (Apple; iPhone12,3)"}

            requests.get(url=lurkurl, headers=lurkheader)
            await asyncio.sleep(3)


async def logout():
    if bearerauth is not None and basicauth is not None:
        daheader = {"Authorization": "Basic " + basicauth,
                    "Ifunny-Project-Id": "iFunny",
                    "User-Agent": "iFunny/7.6.1(21916) iphone/15.1 (Apple; iPhone12,3)"}
    else:
        print("No basic/bearer auth wtf")
        return
    oauthurl = apiurl + "/v4/oauth2/revoke"
    paramz = {'token': bearerauth}
    res = requests.post(url=oauthurl, headers=daheader, data=paramz)
    return res


async def login():
    bearer_path = "my_bearer.txt"
    bearer_file = open(bearer_path, "a+")
    global bearerauth
    if os.path.getsize(bearer_path) != 0:
        bearer_file.seek(0)
        myauth = bearer_file.readline()
        bearerauth = myauth
        myurl = apiurl + "/v4/account"
        myheader = {"Authorization": "Bearer " + bearerauth,
                    "Ifunny-Project-Id": "iFunny",
                    "User-Agent": "iFunny/7.6.1(21916) iphone/15.1 (Apple; iPhone12,3)"}
        resp = requests.get(url=myurl, headers=myheader)
        myacc = resp.json()

        mynick = myacc['data']['nick']
        lout = input(f"You are already logged in as {mynick}. Would you like to log out? (y/n)")
        if lout.lower() == "y":
            didlogout = await logout()
            if didlogout.status_code == 200:
                print("You have been successfully logged out")
                bearer_file.close()
                bearer_file = open(bearer_path, "w+")
                bearer_file.write("")
        else:
            print(f"Ok continuing as {mynick}...")
            await lurk()

    email = input("Enter your email: ")
    passwd = input("Enter your password: ")

    oauthurl = apiurl + "/v4/oauth2/token"

    if basicauth is not None:
        daheader = {"Authorization": "Basic " + basicauth,
                    "Ifunny-Project-Id": "iFunny",
                    "User-Agent": "iFunny/7.6.1(21916) iphone/15.1 (Apple; iPhone12,3)"}
    else:
        print("No basic auth wtf")
        return

    paramz = {'grant_type': 'password',
              'username': email,
              'password': passwd
              }
    if hasPrimed is False or int(round(time.time() * 1000)) - primtime < 10000:
        print("Please allow up to 5-10 secs to log you in for first time...")
        await asyncio.sleep(8)

    resp = requests.post(url=oauthurl, headers=daheader, data=paramz)

    if "invalid_grant" in resp.text:

        print("Invalid login. Please check your credentials." + resp.text)
        sys.exit(-1)

    elif "access_token" in resp.text:
        gettoken = resp.json()
        bearer = gettoken['access_token']

        bearer_file.write(bearer)
        bearer_file.close()

        bearerauth = bearer

        await lurk()

    elif "too_many_user_auths" in resp.text:
        print("Too many auths try logging in later or generate a new 'Basic' auth token if you do not want to wait")
        sys.exit(-1)

    else:
        print("Error could not log you in at this moment.")
        print(resp.json())
        sys.exit(-1)


async def main():
    try:
        prim_path = "primed_basic.txt"
        with open(prim_path, "a+") as bf:
            global basicauth
            if os.path.getsize(prim_path) == 0:
                await asyncio.gather(
                    genAndPrimBasic(),
                    login(),
                )
            else:
                bf.seek(0)
                basicauth = bf.readline()
                global hasPrimed
                hasPrimed = True
                await login()

    except FileNotFoundError:
        await asyncio.gather(
            genAndPrimBasic(),
            login(),
        )


if __name__ == "__main__":
    asyncio.run(main())
