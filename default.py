# -*- coding: utf-8 -*-
# based on dknlght's kodi addon https://github.com/dknlght/dkodi

import httplib
import HTMLParser
import urlparse,urllib,urllib2,re,sys
import cookielib,os,string,cookielib,StringIO,gzip
import os,time,base64,logging
from t0mm0.common.net import Net
import xml.dom.minidom
import xbmcaddon,xbmcplugin,xbmcgui
import json
import urlresolver
import time,datetime
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup
from BeautifulSoup import SoupStrainer
import core
from xml.dom.minidom import Document
from t0mm0.common.addon import Addon
import commands
import jsunpack
import socket

timeout = 60
socket.setdefaulttimeout(timeout)


__settings__ = xbmcaddon.Addon(id='plugin.video.tvbyy')
home = __settings__.getAddonInfo('path')
datapath = xbmc.translatePath(os.path.join(home, 'resources', ''))
strdomain ="http://www.yuezj.com"
net = Net()

def convertascii(strInput, param2, param3):
	strresult=""
	localvar = strInput
	for ctr in range(0, len(param2)): 
		localvar = localvar.replace(param2[ctr], param3[ctr])
	localvar = localvar.replace("%26", "&");
	localvar = localvar.replace("%3B", ";");
	localvar=localvar.replace('<!--?--><?', '<!--?-->')
	strInput = "";
	param2 = "";
	param3 = "";
	return localvar

	
def GetContent(url,retry=0):
    try:
       net = Net()
       second_response = net.http_GET(url, {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.3'})
       rcontent=second_response.content
       try:
            rcontent =rcontent.encode("UTF-8")
       except: pass
       encstring =re.compile('eval\(unescape\((.+?)\)\);').findall(rcontent)
       if(len(encstring)>1):
			rcontent=eval("convertascii("+encstring[1]+")").replace("\/","/") 
       return rcontent
    except:
        if(retry >= 5):
           d = xbmcgui.Dialog()
           d.ok(url,"暫時無法連接",'請重新嘗試')
        else:
            GetContent(url,retry+1)

try:

    DB_NAME = 	 ADDON.getSetting('db_name')
    DB_USER = 	 ADDON.getSetting('db_user')
    DB_PASS = 	 ADDON.getSetting('db_pass')
    DB_ADDRESS = ADDON.getSetting('db_address')

    if  ADDON.getSetting('use_remote_db')=='true' and DB_ADDRESS is not None and DB_USER is not None and DB_PASS is not None and DB_NAME is not None:
        import mysql.connector as database
        print 'Loading MySQL as DB engine'
        DB = 'mysql'
    else:
        print'MySQL not enabled or not setup correctly'
        raise ValueError('MySQL not enabled or not setup correctly')

except:

    try: 
        from sqlite3 import dbapi2 as database
        print 'Loading sqlite3 as DB engine'
    except: 
        from pysqlite2 import dbapi2 as database
        addon.log('pysqlite2 as DB engine')
    DB = 'sqlite'
    db_dir = os.path.join(xbmc.translatePath("special://database"), 'yuezjfav.db')

def initDatabase():
    if DB == 'mysql':
        db = database.connect(DB_NAME, DB_USER, DB_PASS, DB_ADDRESS, buffered=True)
        cur = db.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS favorites (type VARCHAR(10), name TEXT, url VARCHAR(255) UNIQUE, imgurl VARCHAR(255))')
    else:
        if not os.path.isdir(os.path.dirname(db_dir)):
            os.makedirs(os.path.dirname(db_dir))
        db = database.connect(db_dir)
        db.execute('CREATE TABLE IF NOT EXISTS favorites (type, name, url, imgurl)')
    db.commit()
    db.close()
	
def SaveData(SQLStatement): #8888
    if DB == 'mysql':
        db = database.connect(DB_NAME, DB_USER, DB_PASS, DB_ADDRESS, buffered=True)
    else:
        db = database.connect( db_dir )
    cursor = db.cursor()
    cursor.execute(SQLStatement)
    db.commit()
    db.close()

def SaveFav(fav_type, name, url, img):
        if fav_type == '': fav_type = getVideotype(url)
        statement  = 'INSERT INTO favorites (type, name, url, imgurl) VALUES (%s,%s,%s,%s)'
        if DB == 'mysql':
            db = database.connect(DB_NAME, DB_USER, DB_PASS, DB_ADDRESS, buffered=True)
        else:
            db = database.connect( db_dir )
            db.text_factory = str
            statement = statement.replace("%s","?")
        cursor = db.cursor()
        try: 
            cursor.execute(statement, (fav_type, urllib.unquote_plus(unicode(name,'utf-8')), url, img))
            builtin = 'XBMC.Notification(Save Favorite,Added to Favorites,2000)'
            xbmc.executebuiltin(builtin)
        except database.IntegrityError: 
            builtin = 'XBMC.Notification(Save Favorite,Item already in Favorites,2000)'
            xbmc.executebuiltin(builtin)
        db.commit()
        db.close()
		
def AddFavContext(vidtype, vidurl, vidname, vidimg):
        runstring = 'RunScript(plugin.video.yuezj,%s,?mode=22&vidtype=%s&name=%s&imageurl=%s&url=%s)' %(sys.argv[1],vidtype,vidname.decode('utf-8', 'ignore'),vidimg,vidurl)
        cm = add_contextsearchmenu(vidname.decode('utf-8', 'ignore'),vidtype)
        cm.append(('Add to yuezj Favorites', runstring))
        return cm

def BrowseFavorites(section):
    sql = 'SELECT type, name, url, imgurl FROM favorites WHERE type = ? ORDER BY name'
    if DB == 'mysql':
        db = database.connect(DB_NAME, DB_USER, DB_PASS, DB_ADDRESS, buffered=True)
        sql = sql.replace('?','%s')
    else: db = database.connect( db_dir )
    cur = db.cursor()
    cur.execute(sql, (section,))
    favs = cur.fetchall()
    for row in favs:
        title      = row[1]
        favurl      = row[2]
        img      = row[3]
        vtype= row[0]
        fanart = ''
        cm = add_contextsearchmenu(title,vtype)
        remfavstring = 'RunScript(plugin.video.yuezj,%s,?mode=23&name=%s&url=%s)' %(sys.argv[1],urllib.quote_plus(title.encode('utf-8', 'ignore')),urllib.quote_plus(favurl.encode('utf-8', 'ignore')))
        cm.append(('Remove from Favorites', remfavstring))
        if(vtype=="tvshow"):
			nextmode=8
        addDirContext(title.encode('utf-8', 'ignore'),favurl.encode('utf-8', 'ignore'),nextmode,img,"",vtype,cm)
    db.close()

def DeleteFav(name,url): 
    builtin = 'XBMC.Notification(Remove Favorite,Removed '+name+' from Favorites,2000)'
    xbmc.executebuiltin(builtin)
    sql_del = 'DELETE FROM favorites WHERE name=%s AND url=%s'
    if DB == 'mysql':
            db = database.connect(DB_NAME, DB_USER, DB_PASS, DB_ADDRESS, buffered=True)
    else:
            db = database.connect( db_dir )
            db.text_factory = str
            sql_del = sql_del.replace('%s','?')
    cursor = db.cursor()
    cursor.execute(sql_del, (name, url))
    db.commit()
    db.close()
		
def HOME():
        GetMenu()
        #addDir('搜尋（關鍵字）',strdomain,9,'')
        addDir('直接輸入ID',strdomain,10,'')
        addDir('我的最愛','tvshow',25,'')
		
def ListCategories(url,retry=0):
        
        link = GetContent(strdomain+url)
        try:
            link =link.encode("UTF-8")
        except: pass

        if(link == None and retry != 1):
            ListCategories(url, 1)
            return

        newlink = ''.join(link.splitlines()).replace('\t','')
        soup = BeautifulSoup(newlink)
        vidcontent=soup.findAll('div', {"class" : "type_search"})

	alreadyaddedall = 0

        for item in vidcontent[0].findAll('ul')[0].findAll('li')[0].findAll('a'):
			link = item['href'].encode('utf-8', 'ignore')
			vname=str(item.contents[0]).strip()

                        if(vname != '国产剧'):
                            if(vname != '全部' or (vname == '全部' and alreadyaddedall == 0)):
                                addDir(vname,strdomain+"/"+link,18,"")
                                if(vname == '全部'):
                                    alreadyaddedall=1
                                        				
def GetMenu(retry=0):
        link = GetContent(strdomain)
        try:
            link =link.encode("UTF-8")
        except: pass

        if(link == None and retry != 1):
            GetMenu(1)
            return
        
        newlink = ''.join(link.splitlines()).replace('\t','')
        soup  = BeautifulSoup(newlink)
        vidcontent=soup.findAll('ul', {"id" : "cydy-nav"})
        for item in vidcontent[0].findAll('li'):
                if(item != None and item.a != None and item.a['href'] != None):
			link = item.a['href'].encode('utf-8', 'ignore')
			vname=str(item.a.contents[0]).strip()
			print vname.strip()

			
    			if(vname == '排行榜'):
                               addDir(vname,strdomain+link,19,"")
                               continue
                            
			if(vname.strip() != '首页' and vname.strip() != '简洁版'  and vname.strip() != '更多'  and vname.strip() != '地图'):
				addDir(vname,link,15,"")
				
		
def GetVideo(url, retry=0):


        link = GetContent(url)
        try:
            link =link.encode("UTF-8")
        except: pass

        if(link == None and retry != 1):
            GetVideo(url, 1)
            return
        newlink = ''.join(link.splitlines()).replace('\t','')
        
        soup = BeautifulSoup(newlink)
        scriptcontent=soup.findAll('div', {"class" : "clear pl-play js-addDanmu"})

        script = GetContent(strdomain+scriptcontent[0].script["src"])

        if(script == None and retry != 1):
            GetVideo(url, 1)
            return
        
        urlarr = script.split('mac_url=unescape(\'')

        thisNum = url.split("-")
        thisIndex = thisNum[len(thisNum)-2]
        thisNum = thisNum[len(thisNum)-1]
        thisNum = thisNum.split(".")
        thisNum = thisNum[0]


        vid=''
        iframeurl=''

        if(len(urlarr) == 2):
            urlinfo = urlarr[1].split('\')')
            urlinfo = urllib.unquote(urlinfo[0])

            ismixedsources = (urlinfo.find("tudou") > -1 or urlinfo.find("ftp://") > -1 or urlinfo.find("jjhd://") > -1 or urlinfo.find("ffhd://") > -1)

            if(urlinfo.find("$$$") > -1 and ismixedsources):
                mixedsources = 1
            else:
                mixedsources = 0

            urldata = urlinfo.split('$$$')

            i=1
            
            for x in urldata:
                
                #validsource= (x.find("ftp://") == -1 and x.find("jjhd://") == -1 and x.find("ffhd://") == -1);
                #if(x.find("tudou") > -1 or validsource or mixedsources == 0):


                
                if i == int(thisIndex):
                
                    j=1
                    
                    urlepisode= x.split("#")
                    
                    for y in urlepisode:

                        
                        if(int(thisNum) == j):
                            urlepisodeinfo = y.split("$")

                            print "urlepisodeinfo"
                            print urlepisodeinfo
                            if(len(urlepisodeinfo) > 2):
                                    if(urlepisodeinfo[2] == "tudou"):
                                        iframeurl = strdomain+"/player/tudou_t.php?u="+urlepisodeinfo[1]+"&f=tudou&w=100%&h=453"
                                        vid=urlepisodeinfo[1]
                                        
                                    elif(urlepisodeinfo[2] == "yky"):
                                        iframeurl = "http://a.100city.cc/mdparse5/acfun.php?id="+urlepisodeinfo[1]
                                        vid=urlepisodeinfo[1]
                                        
                                    elif(urlepisodeinfo[2] == "bd2"):
                                        iframeurl = "http://t2.tvbyy.com:88/"+urlepisodeinfo[1]+"/1/xml/index.xml"
                                        vid=urlepisodeinfo[1]
                                        
                                    else:
                                        iframeurl = strdomain+"/player/player.php?vid="+urlepisodeinfo[1]
                                        vid=urlepisodeinfo[1]
                                    break
                            else:
                                    if(urlepisodeinfo[1].isdigit()):
                                        iframeurl = strdomain+"/player/tudou_t.php?u="+urlepisodeinfo[1]+"&f=tudou&w=100%&h=453"
                                        vid=urlepisodeinfo[1]
                                    elif(urlepisodeinfo[1].endswith("==")):
                                        iframeurl = "http://a.100city.cc/mdparse5/acfun.php?id="+urlepisodeinfo[1]
                                        vid=urlepisodeinfo[1]
                                    elif(urlepisodeinfo[1].startswith("eq_")):
                                        iframeurl = "http://a.100city.cc/mdparse5/acfun.php?id="+urlepisodeinfo[1]
                                        vid=urlepisodeinfo[1]

                                    else:
                                        iframeurl = strdomain+"/player/player.php?vid="+urlepisodeinfo[1]
                                        vid=urlepisodeinfo[1]
                                    break
                                            
                        j=j+1
                i=i+1
                    


        
        if(iframeurl.find("/player/player.php?vid=") > -1):

            print "iframeurl: "+iframeurl

            
            xmlurl=strdomain+"/player/ning/api/?skey="+vid+"_nly"

            print "xmlurl: "+ xmlurl


            xmllink = GetContent(xmlurl)


            xmlf = re.compile('f->["\']?([^>^"^\']+)["\']?[^>]*}').findall(xmllink)
            
            xmldefatags = re.compile('defa->["\']?([^>^"^\']+)["\']?[^>]*}').findall(xmllink)
            xmldefttags = re.compile('deft->["\']?([^>^"^\']+)["\']?[^>]*}').findall(xmllink)

            xmldefatagsarr = xmldefatags[0].split("|")
            xmldefttagsarr = xmldefttags[0].split("|")

            xmlflink = xmlf[0].split("[$pat]")[0]

            j=0
            for defa in xmldefatagsarr:
                addLink(xmldefttagsarr[j],xmlflink.encode('utf-8', 'ignore')+defa.encode('utf-8', 'ignore'),3,"")
                j=j+1

        iframelink = GetContent(iframeurl)

        print "iframelink"
        print iframelink

        try:
                 iframelink =iframelink.encode("UTF-8")

        except: pass
        if(iframelink == None and retry != 1):
                GetVideo(url,1)
                return

        
        newiframelink = ''.join(iframelink.splitlines()).replace('\t','')

            
        if(newiframelink.find("api.ktkkt") > -1):


            newiframelinkarr1 = newiframelink.split("api.ktkkt")
            newiframelinkdomainarr1 = newiframelinkarr1[0].split("'")
            newiframelinkdomain1 = newiframelinkdomainarr1[len(newiframelinkdomainarr1)-1]
            newiframelinkparamsarr1 = newiframelinkarr1[1].split("'")
            newiframelinkparams1 = newiframelinkparamsarr1[0]


            videolinkm=newiframelinkdomain1+"api.ktkkt"+newiframelinkparams1


            addLink("H264",videolinkm.encode('utf-8', 'ignore'),3,"")

        if(newiframelink.find("365sky") > -1):

            newiframelinkarr2 = newiframelink.split("365sky")
            newiframelinkdomainarr2 = newiframelinkarr2[0].split("\"")
            newiframelinkdomain2 = newiframelinkdomainarr2[len(newiframelinkdomainarr2)-1]
            newiframelinkparamsarr2 = newiframelinkarr2[1].split("\"")
            newiframelinkparams2 = newiframelinkparamsarr2[0]


            videolinkms=newiframelinkdomain2+"365sky"+newiframelinkparams2


 #           addLink("365sky",videolinkms.encode('utf-8', 'ignore'),3,"")


        if(iframeurl.find("api.365sky") > -1):

            xmllink = GetContent(iframeurl)


            xmldefatags = re.compile('defa-&gt;["\']?([^>^"^\']+)["\']?[^>]*}{').findall(xmllink)
            xmldefttags = re.compile('deft-&gt;["\']?([^>^"^\']+)["\']?[^>]*}').findall(xmllink)



            xmldefatagsarr = xmldefatags[0].split("|")
            xmldefttagsarr = xmldefttags[0].split("|")

            j=0
            for defa in xmldefatagsarr:
                addLink(xmldefttagsarr[j],"http://api.365sky.net/mdparse/url.php?"+HTMLParser.HTMLParser().unescape(defa),3,"")
                j=j+1

        if(iframeurl.find("t2.tvbyy") > -1):

            playVideo(iframeurl, "", "")


        if(iframeurl.find("a.100city.cc") > -1):


            xmllink = GetContent("http://a.100city.cc/mdparse5/url.php?xml="+vid+"&type=acfun&hd=gq&wap=0&siteuser=123")



            xmldefatags = re.compile('defa-&gt;["\']?([^>^"^\']+)["\']?[^>]*}{').findall(xmllink)
            xmldefttags = re.compile('deft-&gt;["\']?([^>^"^\']+)["\']?[^>]*}').findall(xmllink)



            xmldefatagsarr = xmldefatags[0].split("|")
            xmldefttagsarr = xmldefttags[0].split("|")

            j=0
            for defa in xmldefatagsarr:
                addLink(xmldefttagsarr[j],"http://a.100city.cc/mdparse5/url.php?"+HTMLParser.HTMLParser().unescape(defa),3,"")
                j=j+1
                
        if(iframeurl.find("/player/tudou_t.php") > -1):

 
        


            newiframelinkarr = newiframelink.split("tudou_t.php")
            newiframelinkdomainarr = newiframelinkarr[0].split("\"")
            newiframelinkdomain = newiframelinkdomainarr[len(newiframelinkdomainarr)-1]
            newiframelinkparamsarr = newiframelinkarr[1].split("\"")
            newiframelinkparams = newiframelinkparamsarr[0]

            videolink=newiframelinkdomain+"tudou_t.php"+newiframelinkparams


            videolinkcontent = GetContent(videolink)


	    xmlrawlink = re.compile('<embed [^>]*flashvars=["\']?([^>^"^\']+)["\']?[^>]*>').findall(videolinkcontent)

            if(len(xmlrawlink) < 1):
                    return
            xmlrawlinkarr = xmlrawlink[0].split("a=")

            xmlrawlinkparam = xmlrawlinkarr[len(xmlrawlinkarr)-1]

            xmlrawlinkurl = xmlrawlinkparam.split("&")[0]

            xmldomain = xmlrawlinkarr[0].split("[$pat]")[0].split("f=")[1]

            vlink= xmldomain.encode('utf-8', 'ignore')+xmlrawlinkurl.encode('utf-8', 'ignore')

            xmllink = GetContent(xmldomain+xmlrawlinkurl)


            xmldefatags = re.compile('defa->["\']?([^>^"^\']+)["\']?[^>]*}').findall(xmllink)
            xmldefttags = re.compile('deft->["\']?([^>^"^\']+)["\']?[^>]*}').findall(xmllink)

            xmldefatagsarr = xmldefatags[0].split("|")
            xmldefttagsarr = xmldefttags[0].split("|")

            j=0
            for defa in xmldefatagsarr:
                addLink(xmldefttagsarr[j],xmldomain.encode('utf-8', 'ignore')+defa.encode('utf-8', 'ignore'),3,"")
                j=j+1
            
        

def CreateList(videoLink):

        print "CreateList"
        liz = xbmcgui.ListItem('[B]PLAY VIDEO[/B]', thumbnailImage="")
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.add(url=videoLink, listitem=liz)
		
def PLAYLIST_VIDEOLINKS(vidlist,name):
        ok=True
        playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playList.clear()
        #time.sleep(2)
        links = vidlist.split(',')
        pDialog = xbmcgui.DialogProgress()
        ret = pDialog.create('正在載入播放列表...')
        totalLinks = len(links)
        loadedLinks = 0
        remaining_display = '已載入 : [B]'+str(loadedLinks)+' / '+str(totalLinks)+'[/B] .'
        pDialog.update(0,'',remaining_display)

        for videoLink in links:

            CreateList(videoLink)
            loadedLinks = loadedLinks + 1
            percent = (loadedLinks * 100)/totalLinks
            #print percent
            remaining_display = '已載入 : [B]'+str(loadedLinks)+' / '+str(totalLinks)+'[/B]'
            pDialog.update(percent,'',remaining_display)
            if (pDialog.iscanceled()):
                return False   
        xbmcPlayer = xbmc.Player()
        xbmcPlayer.play(playList)
        if not xbmcPlayer.isPlayingVideo():
                xbmcPlayer.play(playList)
        return ok
		



def add_contextsearchmenu(title, video_type):
    title=urllib.quote(title.encode('utf-8', 'ignore'))
    contextmenuitems = []
    return contextmenuitems
	

def ParseVideoLink(url,name,movieinfo,retry=0):

    useragent = "|&User-Agent="+urllib.quote_plus("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.36");

    dialog = xbmcgui.DialogProgress()
    dialog.create('加載中', '正在加載中...')       
    dialog.update(0)
    if movieinfo=="direct":
		return url
    link =GetContent(url)
    
    
    if(link == None and retry != 1):
        ParseVideoLink(url, name, movieinfo,1)
        return
    link = ''.join(link.splitlines()).replace('\'','"')

    redirlink=url

    print "redirlink "+ redirlink

    try:
        if (redirlink.find("video.php") > -1):

                vidcontent = GetContent(url)

                vidlinks=re.compile('<file>(.+?)</file>').findall(vidcontent)

                vidlink = ''
                
                if(len(vidlinks)>1):
                    j=0
                    for v in vidlinks:
                        soup = BeautifulSoup(vidlinks[j])
                        for cd in soup.findAll(text=True):
                            vidlinks[j] = cd+useragent
                        
                        j=j+1

                    vidlink=','.join(vidlinks)
                    

                else:
                    soup = BeautifulSoup(vidlinks[0])

                    for cd in soup.findAll(text=True):
                        print "cd:"+ cd
                        vidlink = cd+useragent

        elif (redirlink.find("a.100city.cc") > -1):

                vidcontent = GetContent(url)

                vidlinks=re.compile('<file>(.+?)</file>').findall(vidcontent)

                vidlink = ''
                
                if(len(vidlinks)>1):
                    j=0
                    for v in vidlinks:
                        soup = BeautifulSoup(vidlinks[j])
                        for cd in soup.findAll(text=True):
                            vidlinks[j] = cd+useragent
                        
                        j=j+1

                    vidlink=','.join(vidlinks)
                    

                else:
                    soup = BeautifulSoup(vidlinks[0])

                    for cd in soup.findAll(text=True):
                        print "cd:"+ cd
                        vidlink = cd


        elif (redirlink.find("t2.tvbyy") > -1):
 
                vidcontent = GetContent(url)

        
                vidcontent = ''.join(vidcontent.splitlines()).replace('\t','')

                vidlinks=re.compile('<file>(.+?)</file>').findall(vidcontent)


                vidlink = ''
    
                
                if(len(vidlinks)>1):
                    j=0
                    for v in vidlinks:
                        soup = BeautifulSoup(vidlinks[j])
                        for cd in soup.findAll(text=True):
                            vidlinks[j] = cd
                        
                        j=j+1

                    vidlink=','.join(vidlinks)
                    

                else:
                    soup = BeautifulSoup(vidlinks[0])

                    for cd in soup.findAll(text=True):
                        vidlink = cd

        
        elif (redirlink.find("ktkkt") > -1):

                vidcontent = GetContent(url)


                newlink = ''.join(vidcontent.splitlines()).replace('\t','')
        
                soup = BeautifulSoup(newlink)

                vidcontent=soup.findAll('video')


                vidlinkrdr = vidcontent[0]['src']

                if(vidlinkrdr.find(".mp4") > -1):
                        vidlink = vidlinkrdr+useragent
                else:


                        f = urllib2.urlopen(vidlinkrdr)
                        vidlink = f.geturl()+useragent


 
    
        elif (redirlink.find("365sky") > -1):

                vidcontent = GetContent(url)

                vidlinks=re.compile('<file>(.+?)</file>').findall(vidcontent)

                vidlink = ''
                
                if(len(vidlinks)>1):
                    j=0
                    for v in vidlinks:
                        soup = BeautifulSoup(vidlinks[j])
                        for cd in soup.findAll(text=True):
                            vidlinks[j] = cd+useragent
                        
                        j=j+1

                    vidlink=','.join(vidlinks)
                    

                else:
                    soup = BeautifulSoup(vidlinks[0])

                    for cd in soup.findAll(text=True):
                        print "cd:"+ cd
                        vidlink = cd

 

        elif (redirlink.find("web321") > -1 and redirlink.find("User-Agent") < 0):
 
                vidcontent = GetContent(url)

                vidlinks=re.compile('<file>(.+?)</file>').findall(vidcontent)

                vidlink = ''
    

                
                if(len(vidlinks)>1):
                    j=0
                    for v in vidlinks:
                        soup = BeautifulSoup(vidlinks[j])
                        for cd in soup.findAll(text=True):
                            vidlinks[j] = cd+useragent
                        
                        j=j+1

                    vidlink=','.join(vidlinks)
                    

                else:
                    soup = BeautifulSoup(vidlinks[0])

                    for cd in soup.findAll(text=True):
                        vidlink = cd+useragent

            
    except:
                sources = []
                label=name
                hosted_media = urlresolver.HostedMediaFile(url=redirlink, title=label)
                sources.append(hosted_media)
                source = urlresolver.choose_source(sources)
                if source:
                        vidlink = source.resolve()
    dialog.close()
    if(vidlink == None):
        ParseVideoLink(url,name,movieinfo,1)
        return
    return vidlink


def ListHotShowsCategories(url,retry=0):
       
        link = GetContent(url)
        try:
            link =link.encode("UTF-8")
        except: pass

        if(link == None and retry != 1):
            ListHotShowsCategories(url,1)
            return
        
        newlink = ''.join(link.splitlines()).replace('\t','')

        soup = BeautifulSoup(newlink)
        vidcontent=soup.findAll('dl', {"class" : "first"})
        for item in vidcontent[0].findAll('dd'):

	    if(item.a != None):
                vlink = item.a['href'].encode('utf-8', 'ignore')
		vname=item.a.contents[0].encode('utf-8', 'ignore')
				
		addDir(vname,strdomain+vlink,20,"")
		


def ListHotShows(url,retry=0):
        print url
        link = GetContent(url)
        try:
            link =link.encode("UTF-8")
        except: pass

        print link
        if(link == None and retry != 1):
            ListShows(url,1)
            return
        
        newlink = ''.join(link.splitlines()).replace('\t','')

        soup = BeautifulSoup(newlink)
        vidcontent=soup.findAll('div', {"class" : "top-list"})
        for item in vidcontent[0].findAll('dl'):

                        dt = item.findAll('dt')[1]
                        dd = item.dd
			if(item.has_key("class")==False):
                                ddp = dd.findAll('p')
 
				if(dd.p != None and dd.p.a != None):
					vlink = dd.p.a['href'].encode('utf-8', 'ignore')
					vname=dd.p.a.contents[0].encode('utf-8', 'ignore')
					vimg=strdomain+dt.a.img["src"]
					vplot=""
					if(len(ddp[1].contents)>0):
                                                ddpcontent = ''
                                                if(ddp[1].contents[0] !=  None):
                                                        ddpcontent += str(ddp[1].contents[0]).strip()
                                                        ddpcontent += str(ddp[1].contents[1]).strip()
                                                ddpcontentsub = re.sub('<[^<]+?>', '', ddpcontent)
						vplot=unicode(ddpcontentsub, "utf-8").encode('utf-8', 'ignore')
					addDirContext(vname,strdomain+vlink,8,vimg,vplot,"tvshow")
 


def ListLatest(url,retry=0):
        link = GetContent(url)
        try:
            link =link.encode("UTF-8")
        except: pass

        if(link == None and retry != 1):
            ListShows(url,1)
            return
        
        newlink = ''.join(link.splitlines()).replace('\t','')

        soup = BeautifulSoup(newlink)

        
        vidcontent=soup.findAll('div', {"class" : "class-best1"})
        for item in vidcontent[0].findAll('dl'):

                        dt = item.dt
                        dd = item.dd
			if(item.has_key("class")==False):
   
				if(dt.a != None):

					vlink = dt.a['href'].encode('utf-8', 'ignore')
					vname=dt.a['title'].encode('utf-8', 'ignore')
					vimg=strdomain+dt.a.img["src"]
					
					addDirContext(vname,strdomain+vlink,8,vimg,"","tvshow")
 
		
		
def ListShows(url,retry=0):
        print url
        link = GetContent(url)
        try:
            link =link.encode("UTF-8")
        except: pass

        if(link == None and retry != 1):
            ListShows(url,1)
            return
        
        newlink = ''.join(link.splitlines()).replace('\t','')

        soup = BeautifulSoup(newlink)

        print "url+"+url
        if(url.find("/vod/") > -1):
                
                vname=soup.findAll('span', {"id" : "film_name"})

                print vname
                vimg=soup.findAll('img', {"class" : "poster-cover"})

                print vimg
                addDirContext(vname[0].contents[0].encode('utf-8', 'ignore'),url,8,strdomain+vimg[0]["src"],"","tvshow")
                return

        if(url.find("time.html") < 0 and url.find("new.html") < 0):
            vidcontent=soup.findAll('div', {"class" : "imgListWrp"})[0].findAll('div', {"class" : "imglist02 cl"})
        else:
            ListLatest(url)
            return
        for item in vidcontent[0].findAll('div', {"class":"imgItemWrp"}):



                        dd = item.findAll('div', {"class" : "imgItem"})[0]
                        ddt = item.findAll('div', {"class" : "des toh"})
                        ddp = item.findAll('div', {"class" : "nameWrp toh"})

 
			if(dd.a != None):
					vlink = dd.a['href'].encode('utf-8', 'ignore')
					vname=ddp[0].a.contents[0].encode('utf-8', 'ignore')
					vimg=strdomain+dd.a.img["src"]
					vplot=""
					if(len(ddt) > 0 and ddt[0].a != None and len(ddt[0].a.contents)>0):
                                                ddpcontent = ''
                                                if(ddp[0].contents[0] !=  None):
                                                        ddpcontent += str(ddp[0].contents[0]).strip()
                                                        ddpcontent += str(ddp[0].contents[1]).strip()
                                                ddpcontentsub = re.sub('<[^<]+?>', '', ddpcontent)
						vplot=unicode(ddpcontentsub, "utf-8").encode('utf-8', 'ignore')
					addDirContext(vname,strdomain+vlink,8,vimg,vplot,"tvshow")
        navcontent=soup.findAll('div', {"class" : "pagination m_pagination selfinitModule"})
        if(len(navcontent)>0):
			for item in navcontent[0].findAll('a'):
				vlink=item["href"]
				try:
					vname=item.contents[0].encode('utf-8', 'ignore')
				except:
					vname=item.contents[1].encode('utf-8', 'ignore')
					
				addDir("Page " +vname,strdomain+vlink,18,"")
			
			



def SEARCH(url,type):
        if(type=="keyword"):
            keyb = xbmc.Keyboard('', '輸入關鍵字')
        elif(type=="id"):
            keyb = xbmc.Keyboard('', '輸入ID')
        keyb.doModal()
        searchText = ''
        if (keyb.isConfirmed()):
            searchText = urllib.quote_plus(keyb.getText())
        if(len(searchText.strip())>0):
            if(type=="keyword"):
                url = strdomain+'/index.php?m=vod-search&wd='+searchText
                ListShows(url)
            elif(type == "id"):
                url = strdomain+'/vod/'+searchText+'.html'
                ListShows(url)
		


def Episodes(url,searchbyid=0,retry=0):
        link = GetContent(url)
        try:
            link =link.encode("UTF-8")
        except: pass

        if(link == None and retry != 1):
            Episodes(url,searchbyid,1)
            return
        newlink = ''.join(link.splitlines()).replace('\t','')
        soup = BeautifulSoup(newlink)
        vidcontent=soup.findAll('div', {"id" :re.compile('tab_con')})
        vidimage=soup.findAll('img', {"class" :re.compile('poster-cover')})[0]
 #       vidinfo=soup.findAll('span', {"id" :re.compile('fullContent')})[0]               
            

        for h4item in vidcontent[0].findAll('i'):
                h4 = h4item.findAll('h4')[0]
                if "土豆" not in h4.contents[0].encode('utf-8', 'ignore') and "tudou" not in h4.contents[0].encode('utf-8', 'ignore')  and "云播放" not in h4.contents[0].encode('utf-8', 'ignore')  and "mms" not in h4.contents[0].encode('utf-8', 'ignore') and "yky" not in h4.contents[0].encode('utf-8', 'ignore') and "189" not in h4.contents[0].encode('utf-8', 'ignore'):
                        continue
                for item in h4item.findAll('li'):
			if(item.a==None):
				continue
			else:
				currentitem=item.a
			vlink = currentitem['href'].encode('utf-8', 'ignore')
			if(currentitem.span==None):
				vname=currentitem.contents[0].encode('utf-8', 'ignore')
			else:
				vname=currentitem.span.contents[0].encode('utf-8', 'ignore')
			

			#vplot = vidinfo.h1.contents[0].strip()+"\n\n"

			#for x in vidinfo.dl.contents:
         
    #                        vplot += x.text
 #                           vplot += "\n"

 #                       vplot=vplot.encode('utf-8', 'ignore')

                
                        vlinkfinal = strdomain+vlink
			addDir(vname+h4.contents[0].encode('utf-8', 'ignore'),vlinkfinal,32,strdomain+vidimage["src"],'')


	if len(vidcontent[0].findAll('li')) == 0:
		GetVideo(url)



if os.path.isfile(db_dir)==False:
     initDatabase()
	 
def playVideo(url,name,movieinfo):
        vidurl=ParseVideoLink(url,name,movieinfo);

        if(vidurl.find(",") > -1):

            
	    PLAYLIST_VIDEOLINKS(vidurl, name)
        else:

            xbmcPlayer = xbmc.Player()
                             
            xbmcPlayer.play(vidurl)

def addDirContext(name,url,mode,iconimage,plot="",vidtype="", cm=[]):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&vidtype="+vidtype
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot": plot} )
        if(len(cm)==0):
                contextMenuItems = AddFavContext(vidtype, url, name, iconimage)
        else:
                contextMenuItems=cm
        liz.addContextMenuItems(contextMenuItems, replaceItems=False)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
    	
def addLink(name,url,mode,iconimage,movieinfo=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&movieinfo="+urllib.quote_plus(movieinfo)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        contextMenuItems = []
        liz.addContextMenuItems(contextMenuItems, replaceItems=True)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok
		
def addNext(formvar,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&formvar="+str(formvar)+"&name="+urllib.quote_plus('Next >')
        ok=True
        liz=xbmcgui.ListItem('Next >', iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": 'Next >' } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
		
def addDir(name,url,mode,iconimage,plot=""):
        
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        name=name
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot": plot} )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param    



params=get_params()
url=None
name=None
mode=None
formvar=None
subtitleurl=None
try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        formvar=int(params["formvar"])
except:
        pass		
try:
        subtitleurl=urllib.unquote_plus(params["suburl"])
except:
        pass
try:
        vidtype=urllib.unquote_plus(params["vidtype"])
except:
        pass
try:
        imageurl=urllib.unquote_plus(params["imageurl"])
except:
        pass
try:
        movieinfo=urllib.unquote_plus(params["movieinfo"])
except:
        pass
		
sysarg=str(sys.argv[1]) 

print "currentmode" + str(mode)
if mode==None or url==None or len(url)<1:
        HOME()
elif mode==3:
        playVideo(url,name,movieinfo)
elif mode==8:
        Episodes(url)
elif mode==9:
        SEARCH(url,"keyword")
elif mode==10:
        SEARCH(url,"id")
elif mode==15:
        ListCategories(url)
elif mode==18:
        ListShows(url)
elif mode==19:
        ListHotShowsCategories(url)
elif mode==20:
        ListHotShows(url)
elif mode==22:
        SaveFav(vidtype, name, url, imageurl)
elif mode==23:
        DeleteFav(name,url)
elif mode==25:
        BrowseFavorites(url)
elif mode==28:
        PLAYLIST_VIDEOLINKS(url,name)
elif mode==32:
	GetVideo(url)

xbmcplugin.endOfDirectory(int(sysarg))
