# Author: James Roesemann
# Completed Dec 4th 2022

# SCRIPT DOES NOT FUNCTION AS WRITTEN. IT IS FOR DEMONSTRATION PURPOSES ONLY.
# This python script was originally written as an exercise to teach me how to web scrape.
# A webcomic I've been reading for years was ending it's run and I wanted to preserve it.
# The website has always been self hosed and I wasn't sure how long the artist would keep it up after completion.
# I'm a bit embarrassed by it. I've scrubbed this version of the script of all mention of site.
# Anything that's been redacted has been replaced with a string describing what used to be there in capital letters.
# Unfortunately, without this information, the script does not function.
# I hope this example at least demonstrates my ability as a programmer even if it is non functional.



# imports
import os
from pickle import NONE
from types import NoneType
import urllib.request
from xmlrpc.client import Boolean, boolean
import bs4
from bs4 import BeautifulSoup
import requests
import sys
import random
import jsbeautifier
import ssl
from requests.exceptions import ConnectionError

#class definitions
#this class contains the pageID for the first pages, and the chapter name of every first page found in the dropdown.js s
class FirstPage:
    def __init__(self, chapterName, firstPageId): 
        self.chapterName = chapterName 
        self.firstPageId = firstPageId


# function definitions
# given a string, remove characters that the windows file system would consider illegal or otherwise cause a problem.
def leaglize(inData:str)-> str:
        invalid='<>:\"/\\|?*\t'
        for i in invalid:
            inData=inData.replace(i, '')
        return inData

# given the current working directory and a archiveName, makes a new directory unless one of that name already exists. 
# returns string to use as working directory in other functions
def createDir(cwd, chapterNum):
    legalName=leaglize(str(chapterNum))
    if not os.path.exists(cwd + "\\" + legalName):
        os.mkdir(cwd + "\\" + legalName)
    return cwd + "\\" + legalName

# given a url string, extract the file name from it and return it as a string.
def getFileId(fileUrl:str) ->str:
    fowardSlashPos = fileUrl.rfind("/")
    fileName = fileUrl[fowardSlashPos + 1 :]
    return fileName

# given strings for file url,directory and page name, download that file to the directory.
def downloadPage(fileUrl:str, currentDirectory:str, pageName:str):
    fileName = pageName+" " +getFileId(fileUrl)
    fileUrl=fixUrl(fileUrl)
    finalFileName=currentDirectory + "\\" + fileName
    if not os.path.exists(finalFileName):
        urllib.request.urlretrieve(fileUrl, finalFileName)

# given a bs4.element.Tag object, extract the the page url/urls and return as a bs4.element.Tag object
def findAllImgUrls(scrapedPage:'bs4.BeautifulSoup') -> 'bs4.BeautifulSoup':
    imgUrls=scrapedPage.find_all('img')
    return imgUrls

# given a bs4.element.Tag object, find the url with a src tag. return as a string.
def getImageUrl(scrapedPage:'bs4.BeautifulSoup') -> str:
    return str(scrapedPage.get('src'))

# given a bs4.element.Tag object,find the url with the name="value" tag. return as a string
def getValueUrl(scrapedPage:'bs4.BeautifulSoup')-> str:
    return str(scrapedPage.get("value"))

#given a bs4.element.Tag object, extract the line with the page short_name and return as a string
def getShortName(scrapedPage:'bs4.BeautifulSoup') -> str:
    pageShortName=scrapedPage.find('span', id="page_shortname")
    return str(pageShortName)

# test if the url (in the form of a string) has WEBSITE_NAME_REDACTED in it.
# if not add it to the appropriate location and return as a string.
def fixUrl(url:str) -> str:
    #aparently any white spaces in the url needs to be changed to %20 in order to function properly.
    url=url.replace(' ','%20')
    if not 'WEBSITE_NAME_REDACTED' in url:
        return('BASE_WEBSITE_URL_REDACTED'+url)
    else:
        return(url)

# given a string object, return the page number/name.
def getWebsitePageName(pageShortName:str) -> str:
    startPos=pageShortName.find(': ')
    endPos=pageShortName.find('</span>')
    return pageShortName[startPos+2:endPos]

# given a bs4.element.Tag object, find the pageID value for the next page. 
# return as a string containing the pageID.
# if at the end of chapter, returns "EndOfChapter"
def getWebsiteNextPageId(scrapedPage:'bs4.BeautifulSoup') -> str:
    #accounting for the fact that the page format is diffrent for some chapters.
    inClass=False
    pageId=str(scrapedPage.find('a', id='link_next_top'))
    if pageId=='None':
        pageId=str(scrapedPage.select_one('.Link_Next'))
        inClass=True

    #if pageId still equals 'None' at this point, then it's the end of the chapter. return "EndOfChapter"
    if pageId=='None':
        return "EndOfChapter"
    else:
        startPos=pageId.find('sid=')
        #if the data is in a class
        if inClass==True:
            endPos=pageId.find('\"></')
            return (pageId[startPos+4:endPos])
        #if the data was found the regular way      
        else:
            endPos=pageId.rfind('id=')
            return (pageId[startPos+4:endPos-2])
        

# given a bs4.element.Tag object, use find_all to search for the line or lines with the img tag. 
# return a bs4.element.Tag object with the line/lines. 
# if no line exists the value will be None
def isImgPresent(scrapedPage:'bs4.BeautifulSoup') -> 'bs4.BeautifulSoup':
    return scrapedPage.find_all('img')

# given a bs4.element.Tag object, use select to search for a line with the param name ="movie". 
# return a bs4.element.Tag object with the line/lines. 
# if no line exists the value will be None
def isMoviePresent(scrapedPage:'bs4.BeautifulSoup') -> 'bs4.BeautifulSoup':
    return scrapedPage.select("param[name*='movie']")

# given a bs4.element.Tag object and strings for the directory and page name, iterate through all tuples and download all the main images on that page.
def downloadMainImages(scrapedPage:'bs4.BeautifulSoup', currentDirectory, pageName):
    for i in range(len(scrapedPage)):
        imageUrl=(getImageUrl(scrapedPage[i]))
        downloadPage(imageUrl, currentDirectory, pageName)

#given a bs4.element.Tag object and strings for the directory and page name, iterate through all tuples and download all the main content other than images on that page
def downloadAltContent(scrapedPage:'bs4.BeautifulSoup', currentDirectory,pageName):
    for i in range(len(scrapedPage)):
        movieUrl=(getValueUrl(scrapedPage[i]))
        downloadPage(movieUrl, currentDirectory,pageName)

# this function creates a session and returns a session object
def openSession():
    sessionRequest = requests.session()
    return sessionRequest

# givin a session, string for loginURL and loginData, submits a post request to the site. 
# returns notniing.
def loginToSite(openSession:requests.session, loginURL:str, loginData):
    openSession.post(loginURL, loginData)

# given a session and a dropdownURL,download the returned unfomated data and save as dropDown.js in the working directory
# I found it necessary to export the data to a file because for some reason the json data is not being formatted in a useable was as a string object, but it does seem to work if read in line by line from a text file. 
def getDropdown(currentSession:requests.session, currentURL):
    workingDir = os.path.realpath(os.path.dirname(__file__))
    pageRequest=currentSession.get(currentURL)
    scrapedPage=BeautifulSoup(pageRequest.text, "html.parser")
    fixedJson=jsbeautifier.beautify(scrapedPage.prettify())
    outFile = open(workingDir+"\dropDown.js","w") 
    outFile.write(fixedJson)
    outFile.close()

# loads the data from dropDown.js, splits every line in the list. 
# searches for lines containing the keyword "Pages:" and returns a list comprised of the next line after the keyword, which would contain the id of the first page of a given chapter.
# must run after getDropDown or will return outdated results
def extractFirstPages() -> FirstPage:
    workingDir = os.path.realpath(os.path.dirname(__file__))
    if not os.path.exists(workingDir+"\dropDown.js"):
        sys.stderr.write('Error: dropDown.js could not be found\n')
        return
    inData = open(workingDir+"\dropDown.js").readlines()
    pagesData=[]
    chapterData=[]
    outData=[]
    for i in range(len(inData)):
        containesPages=inData[i].find("Pages:")
        if containesPages!=-1:
            #first page Id
            pagesData.append(inData[i+1])
            #chapter name Id
            chapterData.append(inData[i-2])
        containesPages=-1
    #cleanup pages data
    for i in range(len(pagesData)):
        pagesData[i]=pagesData[i].strip("ID: ")
        pagesData[i]=pagesData[i].rstrip(",\n")
    #clean up chapter name data
    for i in range(len(chapterData)):
        chapterData[i]=chapterData[i].strip("Name: ")
        chapterData[i]=chapterData[i].rstrip(",\n")
        #append to outdata
        outData.append(FirstPage(chapterData[i], pagesData[i]))    
    return outData

# given a session and a list of dropdown url strings,executes getDropDown and extractFirstPages. 
# returns a 2d list with all the chapter first pages
## returns a list of all the first page data
def getAllFirstPages(currentSession:requests.session, dropDownURLs:list):
    outData=[]
    for i in range(len(dropDownURLs)):
        getDropdown(currentSession, dropDownURLs[i])
        temp=extractFirstPages()
        outData.append(temp)
    #cleanup the dropDown.js file. should defnitly already exist if getDropdown executed
    workingDir = os.path.realpath(os.path.dirname(__file__))
    os.remove(workingDir+"\dropDown.js")
    return outData

# given a url, extract the archive name and return as a string
def getArchiveName(url:str):
    pos1=url.find("REDACTED_WEBSITE_URL_PORTION")
    pos2=url.find(".php")
    return url[pos1+10:pos2]

# given a bs4.element.Tag object, return a bs4.element.Tag with only the middle content
def getMainContent(scrapedPage:'bs4.BeautifulSoup') -> 'bs4.BeautifulSoup':
    pageContent=scrapedPage.find('div', id="float_wrap")
    #if this page is using the PageContainer style as aposed to the float_wrap syle run this conditional to exttract pageContent
    if pageContent==None:
        pageContent=scrapedPage.find('div', id="MainBox")
    return(pageContent)

# given a bs4.element.Tag object, return a bs4.element.Tag with only the head content
def getStylesheet(scrapedPage:'bs4.BeautifulSoup') -> bs4.element.ResultSet:
    pageContent=scrapedPage.find_all('link', rel='stylesheet')
    return((pageContent))

# given a bs4.element.ResultSet, search for the one containing archive_themes, 
# return a string contaiing the archive theme text needed to build a link  
def getArchiveTheme(inData:bs4.element.ResultSet):
    for i in range(len(inData)):
        if "archive_themes" in str(inData[i]):
            pos1=str(inData[i]).find("archive_themes")
            pos2=str(inData[i]).rfind("/css/archive.css")
            return str(inData[i])[pos1+15:pos2]

# given a bs4.element.Tag, check if the background has already beed downloaded, and if not download it
def downloadWebsiteBackground(scrapedPage:'bs4.BeautifulSoup', currentDirectory:str):
    archiveTheme=(getArchiveTheme(getStylesheet(scrapedPage)))
    archiveUrl="REDACTED_WEBSITE_URL/archive_themes/"+archiveTheme+"/pics/background.jpg"
    if not os.path.exists(currentDirectory+"\\Backgrounds"):
        os.mkdir(currentDirectory+"\\Backgrounds")
    if not os.path.exists(currentDirectory+"\\Backgrounds\\"+archiveTheme+'.jpg'):
        try:
            finalFile=currentDirectory+"\\Backgrounds\\"+archiveTheme+".jpg"
            if not os.path.exists(finalFile):
                urllib.request.urlretrieve(archiveUrl, finalFile)  
        except:
            archiveUrl="REDACTED_WEBSITE_URL/archive_themes/"+archiveTheme+"/pics/mable-bg.png"
            finalFile=currentDirectory+"\\Backgrounds\\"+archiveTheme+".png"
            if not os.path.exists(finalFile):
                urllib.request.urlretrieve(archiveUrl, currentDirectory+"\\Backgrounds\\"+archiveTheme+".png")  
            


# recursive function. 
# given strings for the wokring directory, core url , page id and page numbers, download the pages to the working directory. 
# when at the end of the chapter, return on completion.
# make sure current chapter archive is already created and passed the working directory before invoking.
# returns nothing.
def turnPages(workingDir:str, coreUrl:str, pageId:str, pageNumber:int):
    # prints a '.' to screen to let you know the program is still working, but dosent run evey fuction call. 
    x=random.randint(0,9)
    if x == 1:
        print('.', end="")
    # thesres a chance there could be an exeption here. 
    # it's hard for me to reproduce
    # lets see if this is a connection error or the server is cuting me off.
    while True:
        try:    
            pageRequest=currentSesion.get(coreUrl+pageId)
        except ConnectionError as e:
            print(e)
            print("ConnectionError exception")
            pageRequest="no response"
            continue
        break
    scrapedPage=BeautifulSoup(pageRequest.text, "html.parser")
    # this extracts the shortname, which contains the page name and number
    shortName=getShortName(scrapedPage)
    nextPageId=getWebsiteNextPageId(scrapedPage)
    # get and set the page name
    pageName=getWebsitePageName(shortName)
    pageName=leaglize(pageName)
    pageName=str(pageNumber)+' '+pageName
    pageNumber+=1
    # main content section contains most of the relevent content, except backgrounds
    pageContent=getMainContent(scrapedPage)
    downloadAltContent(isMoviePresent(pageContent), workingDir,pageName)
    #download the main content, if available
    downloadMainImages(findAllImgUrls(pageContent), workingDir, pageName)
    #download the background if it hasen't already
    downloadWebsiteBackground(scrapedPage,workingDir)
    #if at the end of the chapter, print "EndOfChapter" to screen and return.
    # If not, call this function again with the nextPageId
    if(nextPageId=="EndOfChapter"):
        print(nextPageId)
        return
    else:
        turnPages(workingDir,coreUrl,nextPageId,pageNumber)

# given strings for  the working directory, a core Url, and a list of FirstPage objects, establish a directory for the current chapter and invoke turnPages
# returns nothing.
def getChapters(workingDir, coreURL, startingPoints:list):
    for i in range(len(startingPoints)):
        legalName=leaglize(startingPoints[i].chapterName)
        currentWorkingDir=createDir(workingDir, legalName)
        turnPages(currentWorkingDir,coreURL,startingPoints[i].firstPageId,1)








#main

loginURL='REDACTED_WEBSITE_LOGINBAR_URL'
loginData = {
    'ajax': 'true',
    'action': 'login',
    'username': 'REDACTED_USERNAME',
    'password': 'REDACTED_PASSWORD',
}

# starting URLs. each story archive is has it's own url
# I have to add the urls manualy like this beacuse there is no easily searchable way to find these archives. 
# they change position on the webpage as pages are added to them.
# make sure the order of these URLs match the order of the dropdown menu URLs.
corePageURLs=[]
corePageURLs.append("REDACTED_STORY_ARCHIVE_URL_1")
corePageURLs.append("REDACTED_STORY_ARCHIVE_URL_2")
corePageURLs.append("REDACTED_STORY_ARCHIVE_URL_3")
corePageURLs.append("REDACTED_STORY_ARCHIVE_URL_4")
corePageURLs.append("REDACTED_STORY_ARCHIVE_URL_5")
corePageURLs.append("REDACTED_STORY_ARCHIVE_URL_6")
#archive dropdown menu URLs
dropDownURLs=[]
dropDownURLs.append("REDACTED_STORY_ARCHIVE_DROPDOWN_MENU_URL_1")
dropDownURLs.append("REDACTED_STORY_ARCHIVE_DROPDOWN_MENU_URL_2")
dropDownURLs.append("REDACTED_STORY_ARCHIVE_DROPDOWN_MENU_URL_3")
dropDownURLs.append("REDACTED_STORY_ARCHIVE_DROPDOWN_MENU_URL_4")
dropDownURLs.append("REDACTED_STORY_ARCHIVE_DROPDOWN_MENU_URL_5")
dropDownURLs.append("REDACTED_STORY_ARCHIVE_DROPDOWN_MENU_URL_6")

#create the starting directories
workingDir = os.path.realpath(os.path.dirname(__file__))
workingDir += "\\WEBSITE_NAME_REDACTED"
if not os.path.exists(workingDir):
    os.mkdir(workingDir)

#this website still dosn't have a trusted ssl certificate, so I need to create an unverified context in ssl
ssl._create_default_https_context=ssl._create_unverified_context

#start session
currentSesion=openSession()
loginToSite(currentSesion, loginURL, loginData)

#get the page id of the first page of every chapter
chapterFirstPages=getAllFirstPages(currentSesion, dropDownURLs)

#iterate through all the archives
for i in range(len(corePageURLs)):
    currentArchive=getArchiveName(corePageURLs[i])
    currentWorkingDir=createDir(workingDir, currentArchive)
    #start each of the chapters here
    getChapters(currentWorkingDir,corePageURLs[i],chapterFirstPages[i])
    print("Finished archive "+currentArchive)
print("\nDone")