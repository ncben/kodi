# -*- coding: utf-8 -*-
# based on dknlght's kodi addon https://github.com/dknlght/dkodi

import httplib
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

timeout = 5
socket.setdefaulttimeout(timeout)


__settings__ = xbmcaddon.Addon(id='plugin.video.tvbyy')
home = __settings__.getAddonInfo('path')
datapath = xbmc.translatePath(os.path.join(home, 'resources', ''))
strdomain ="http://tvbyy.com"
AZ_DIRECTORIES = ['0','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y', 'Z']
net = Net()
class InputWindow(xbmcgui.WindowDialog):# Cheers to Bastardsmkr code already done in Putlocker PRO resolver.
    def __init__(self, *args, **kwargs):
        self.cptloc = kwargs.get('captcha')
        self.img = xbmcgui.ControlImage(335,20,624,180,self.cptloc)
        self.addControl(self.img)
        self.kbd = xbmc.Keyboard()

    def get(self):
        self.show()
        self.kbd.doModal()
        if (self.kbd.isConfirmed()):
            text = self.kbd.getText()
            self.close()
            return text
        self.close()
        return False
		
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
    db_dir = os.path.join(xbmc.translatePath("special://database"), 'tvbyyfav.db')

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

def HostResolver(url):
		print "in HostResolver"
		parsed_uri = urlparse.urlparse(url)
		server=str(parsed_uri.netloc)
		server=server.split(".")
		if(len(server)>2):
			server=server[1]
		else:
			server=server[0]
		server=server.replace("180upload","one80upload")
		exec "from servers import "+server+" as server_connector"
		rtnstatus,msg = server_connector.test_video_exists( page_url=url )
		if(rtnstatus):
			video_urls = server_connector.get_video_url( page_url=url , video_password="" )
			return video_urls[0][1]
		else:
			return ""
		
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
        runstring = 'RunScript(plugin.video.tvbyy,%s,?mode=22&vidtype=%s&name=%s&imageurl=%s&url=%s)' %(sys.argv[1],vidtype,vidname.decode('utf-8', 'ignore'),vidimg,vidurl)
        cm = add_contextsearchmenu(vidname.decode('utf-8', 'ignore'),vidtype)
        cm.append(('Add to tvbyy Favorites', runstring))
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
        remfavstring = 'RunScript(plugin.video.tvbyy,%s,?mode=23&name=%s&url=%s)' %(sys.argv[1],urllib.quote_plus(title.encode('utf-8', 'ignore')),urllib.quote_plus(favurl.encode('utf-8', 'ignore')))
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
        addDir('搜尋（關鍵字）',strdomain,9,'')
        addDir('搜尋（ID)',strdomain,10,'')
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
        vidcontent=soup.findAll('div', {"class" : "main"})

	alreadyaddedall = 0

        for item in vidcontent[0].findAll('li'):
			link = item.a['href'].encode('utf-8', 'ignore')
			vname=str(item.a.contents[0]).strip()

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
        vidcontent=soup.findAll('div', {"class" : "nav"})
        for item in vidcontent[0].findAll('li'):
			link = item.a['href'].encode('utf-8', 'ignore')
			vname=str(item.a.contents[0]).strip()
			print vname.strip()

			
    			if(vname == '排行榜'):
                               addDir(vname,strdomain+link,19,"")
                               continue
                            
			if(vname.strip() != '首页'):
				addDir(vname,link,15,"")
				
		
def SensenGetVideo(url, retry=0):
    
        link = GetContent(url)
        try:
            link =link.encode("UTF-8")
        except: pass

        if(link == None and retry != 1):
            SensenGetVideo(url, 1)
            return
        newlink = ''.join(link.splitlines()).replace('\t','')
        
        soup = BeautifulSoup(newlink)
        scriptcontent=soup.findAll('div', {"class" : "l"})

        script = GetContent(strdomain+scriptcontent[0].script["src"])

        if(script == None and retry != 1):
            SensenGetVideo(url, 1)
            return
        
        urlarr = script.split('mac_url=unescape(\'')

        thisNum = url.split("-")
        thisNum = thisNum[len(thisNum)-1]
        thisNum = thisNum.split(".")
        thisNum = thisNum[0]

        vid=''

        if(len(urlarr) == 2):
            urlinfo = urlarr[1].split('\')')
            urlinfo = urllib.unquote(urlinfo[0])

            ismixedsources = (urlinfo.find("tudou") > -1 or urlinfo.find("ftp://") > -1 or urlinfo.find("jjhd://") > -1 or urlinfo.find("ffhd://") > -1)

            if(urlinfo.find("$$$") > -1 and ismixedsources):
                mixedsources = 1
            else:
                mixedsources = 0

            urldata = urlinfo.split('$$$')

            for x in urldata:
                validsource= (x.find("ftp://") == -1 and x.find("jjhd://") == -1 and x.find("ffhd://") == -1);
                if(x.find("tudou") > -1 or validsource or mixedsources == 0):
                    urlepisode= x.split("#")
                    j=1
                    for y in urlepisode:
                        urlepisodeinfo = y.split("$")
                        if(int(thisNum) == j):
                            if(urlepisodeinfo[1].isdigit()):
                                iframeurl = strdomain+"/player/tudou_t.php?u="+urlepisodeinfo[1]+"&f=tudou&w=100%&h=453"
                                vid=urlepisodeinfo[1]
                            else:
                                iframeurl = strdomain+"/player/player.php?vid="+urlepisodeinfo[1]
                                vid=urlepisodeinfo[1]
                                break
                        j=j+1
                    
        
        if(iframeurl.find("/player/player.php?vid=") > -1):

            xmlurl=strdomain+"/player/ning/api/?skey="+vid+"_nly"


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
            

        if(iframeurl.find("/player/tudou_t.php") > -1):

            iframelink = GetContent(iframeurl)
            try:
                iframelink =iframelink.encode("UTF-8")
            except: pass

            if(iframelink == None and retry != 1):
                SensenGetVideo(url,1)
                return
        
            newiframelink = ''.join(iframelink.splitlines()).replace('\t','')

            newiframelinkarr = newiframelink.split("tudou_tvbyy.php")
            newiframelinkdomainarr = newiframelinkarr[0].split("\"")
            newiframelinkdomain = newiframelinkdomainarr[len(newiframelinkdomainarr)-1]
            newiframelinkparamsarr = newiframelinkarr[1].split("\"")
            newiframelinkparams = newiframelinkparamsarr[0]

            videolink=newiframelinkdomain+"tudou_tvbyy.php"+newiframelinkparams

            videolinkcontent = GetContent(videolink)

	    xmlrawlink = re.compile('<embed [^>]*flashvars=["\']?([^>^"^\']+)["\']?[^>]*>').findall(videolinkcontent)

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
                #d = xbmcgui.Dialog()
                #d.ok('videourl: ' + str(playList), 'One or more of the playlist items','Check links individually.')
        return ok
		



def add_contextsearchmenu(title, video_type):
    title=urllib.quote(title.encode('utf-8', 'ignore'))
    contextmenuitems = []
    return contextmenuitems
	

def ParseVideoLink(url,name,movieinfo,retry=0):
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

    try:
        if (redirlink.find("tvbyy.com/player/ning/api") > -1):

                vidcontent = GetContent(url)

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
                        print "cd:"+ cd
                        vidlink = cd

        
        elif (redirlink.find("web321") > -1 and redirlink.find("User-Agent") < 0):
 
                vidcontent = GetContent(url)

                vidlinks=re.compile('<file>(.+?)</file>').findall(vidcontent)

                vidlink = ''
    
                useragent = "|&User-Agent="+urllib.quote_plus("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.36");

                
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
        link = GetContent(url)
        try:
            link =link.encode("UTF-8")
        except: pass

        if(link == None and retry != 1):
            ListShows(url,1)
            return
        
        newlink = ''.join(link.splitlines()).replace('\t','')

        soup = BeautifulSoup(newlink)

        if(url.find("time.html") < 0 and url.find("new.html") < 0):
            vidcontent=soup.findAll('div', {"class" : "left"})
        else:
            ListLatest(url)
            return
        for item in vidcontent[0].findAll('dl'):

                        dt = item.dt
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
        navcontent=soup.findAll('div', {"class" : "page1"})
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
                Episodes(url,1)
		


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
        vidcontent=soup.findAll('div', {"class" :re.compile('play-list')})
        vidimage=soup.findAll('div', {"class" :re.compile('pic')})[0]
        vidinfo=soup.findAll('div', {"class" :re.compile('info')})[0]

        if(searchbyid == 1):
            searchText = urllib.quote_plus(vidinfo.h1.contents[0].strip().encode('utf-8', 'ignore'))
            if(len(searchText.strip())>0):
                url = strdomain+'/index.php?m=vod-search&wd='+searchText
                ListShows(url)
                return                
            

        for item in vidcontent[0].findAll('li'):
			if(item.span==None):
				currentitem=item.a
			else:
				currentitem=item.span.a
			vlink = currentitem['href'].encode('utf-8', 'ignore')
			if(currentitem.span==None):
				vname=currentitem.contents[0].encode('utf-8', 'ignore')
			else:
				vname=currentitem.span.contents[0].encode('utf-8', 'ignore')
			

			vplot = vidinfo.h1.contents[0].strip()+"\n\n"

			for x in vidinfo.dl.contents:
         
                            vplot += x.text
                            vplot += "\n"

                        vplot=vplot.encode('utf-8', 'ignore')

			addDir(vname,strdomain+vlink,32,strdomain+vidimage.img["src"],vplot)


	if len(vidcontent[0].findAll('li')) == 0:
		SensenGetVideo(url)



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
	SensenGetVideo(url)

xbmcplugin.endOfDirectory(int(sysarg))
