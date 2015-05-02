import re
import traceback

def parseUserAgent(useragent):
    uasplit = splitUserAgent(useragent)
    if not uasplit:
        return {}
    
    if not seemsLikeANormalUA(useragent):
        return None#{'text': useragent}

    parsed = {}
    url = getURLFromUA(useragent)
    if url is not None:
        parsed.update({'url': url})
    
    agent = splitVersion(uasplit[0].strip(';'))
        
    if len(uasplit) == 1:
        parsed.update({'browser': agent})
        return parsed

    elif agent[0] == 'Mozilla':
        platform = uasplit[1].strip('()').split('; ')
        #if platform[0] == 'compatible':
        #    return parseUserAgent('; '.join(platform[1:])) # very hacky!
        info = uasplit[2:]
        try:
            new = parseMozilla(platform, info)
            if new is not None:
                parsed.update(new)
                return parsed
            else:
                return None
        except:
            traceback.print_exc()
            return None
        
    elif agent[0] == 'curl':
        parsed.update({'browser': splitVersion(uasplit[0]), 'os': uasplit[1].strip('()')})
        return parsed
    else:
        parsed.update({'browser': agent})
        return parsed
    
    #return parsed
    return None

def seemsLikeANormalUA(useragent):
    try:
        useragent.encode('ascii')
    except UnicodeDecodeError:
        return False
    if len(useragent.split()) == 1:
        return True
    if re.search('\.[0-9]', useragent):
        return True
    points = 0
    if getURLFromUA(useragent) is not None:
        points += 1
    if '; ' in useragent:
        points += 1
    if re.search('\([^)]+\)', useragent):
        points += 1
    if re.search('[0-9]\.[0-9]', useragent):
        points += 1
    if re.search('^[A-Z][a-z]', useragent):
        points += 1
    return points >= 3

def getURLFromUA(useragent):
    if 'http://' in useragent:
        url_start = useragent[useragent.find('http://'):]
    elif 'https://' in useragent:
        url_start = useragent[useragent.find('https://'):]
    else:
        return None
    url = url_start.split()[0].strip(')').strip(',')
    return url

def parseMozilla(platform, info):
    if platform[0] in ['compatible', 'Mobile']:
        if platform[1].startswith('MSIE'):
            browser = ('Internet Explorer', version(platform[1].split()[1]))
            os_string = platform[2]
            osname = os_string.rsplit(' ', 1)[0]
            osver = version(os_string.split()[-1])
            if osname == 'Windows Phone OS':
                osname = 'Windows Phone'
            if osname == 'Windows Phone':
                device = '%s %s' % (platform[-2], platform[-1])
                return {'browser': browser, 'os': (osname, osver), 'device': device}
            else:
                return {'browser': browser, 'os': (osname, osver)}
        else:
            return {'browser': splitVersion(platform[1])}
    
    if len(info) < 2:
        return None

    
    # Firefox
    if info[1].startswith('Firefox/') and info[0].startswith('Gecko/'):
        browser = splitVersion(info[-1]) # Gecko/20100101 Firefox/34.0.1 Waterfox/34.0
        revision = platform.pop()
        client = {'browser': browser}
        if revision.startswith('rv:'):
            os = None
            if platform[0] == 'Android':
                os = ('Android', [])
            elif platform[0] == 'Macintosh':
                osname = 'Mac OS X'
                h = re.match(r'Intel Mac OS X ([0-9_]*)', platform[1])
                if h is not None:
                    osver = h.group(1)
                else:
                    osver = ''
                os = (osname, version(osver))
            elif platform[0] == 'X11':
                os = (platform[1].split()[0], [])
            elif platform == ['Maemo', 'Linux', 'U', 'Jolla', 'Sailfish', 'Mobile']:
                os = ('Jolla', [])
            elif platform[0].startswith('Windows'):
                if platform[0] == 'Windows':
                    platform.pop(0)
                if platform[0] == 'U':
                    platform.pop(0)
                os_string = platform.pop(0)
                osname = os_string.rsplit(' ', 1)[0]
                osver = version(os_string.split()[-1])
                os = (osname, osver)
            else:
                print(platform)
            if os is not None:
                client.update({'os': os})
            #return 'bot', browser
        return client
        #return platform, browser
    if platform[0] in ['iPad', 'iPhone', 'iPod', 'iPod touch']:
        osname = 'iOS'
        osver = re.match(r'CPU (iPhone )?OS ([0-9_]*) like Mac OS X', platform[-1]).group(2)
        os = (osname, version(osver))
        device = platform[0]
        browser = parseWebKitTail(info)
        if browser is not None:
            bname, bver = browser
            if bname == 'Mobile':
                browser = 'unknown'
                # TODO how should we differentiate it is not possible to know
                # and we could not parse it
            else:
                if bname == 'Version':
                    bname = 'Safari'
                elif bname == 'CriOS':
                    bname = 'Chrome'
                browser = (bname, bver)
        #return
        return {'device': device, 'os': os, 'browser': browser}
    if platform[0] == 'Macintosh':
        osname = 'Mac OS X'
        h = re.match(r'Intel Mac OS X ([0-9_]*)', platform[-1])
        if h is not None:
            osver = h.group(1)
        else:
            return None
        os = (osname, version(osver))
        device = platform[0]
        browser = parseWebKitTail(info)
        if browser is not None:
            bname, bver = browser
            if bname == 'Version':
                bname = 'Safari'
            browser = (bname, bver)
        #return
        return {'device': device, 'os': os, 'browser': browser}
    if platform[0] == 'Linux': # android
        # in rare cases, Build code is informative
        # 'Android 4.4.2', 'LG-D620 Build/KOT49I.A1401238405'
        # 'Android 4.4.2', 'LG-D620 Build/KOT49I.A1404447153'
        if platform[1] == 'U':
            platform.pop(1)
        osname, osver = platform[1].split()
        osver = version(osver)
        os = (osname, osver)
        if ' ' in platform[-1]:
            device, build = platform[-1].rsplit(' ', 1)
        else:
            device = None
        browser = parseWebKitTail(info)
        if browser is not None:
            bname, bver = browser
            if bname == 'Version':
                bname = 'Android browser'
            browser = (bname, bver)
        #return
        return {'device': device, 'os': os, 'browser': browser }

    if platform[0].startswith('Windows'):
        if platform[0] == 'Windows':
            platform.pop(0)
        if platform[0] == 'U':
            platform.pop(0)
        os_string = platform.pop(0)
        osname = os_string.rsplit(' ', 1)[0]
        osver = version(os_string.split()[-1])
        os = (osname, osver)
        if 'Trident/7.0' in platform:
            browser = ('Internet Explorer', [11])
        else:
            browser = parseWebKitTail(info)
        if osname == 'Windows Phone':
            device = '%s %s' % (platform[-2], platform[-1])
            return {'browser': browser, 'os': os, 'device': device}
        else:
            return {'browser': browser, 'os': os}
    
    if platform[0] == 'MeeGo':
        browser = parseWebKitTail(info)
        device = platform[1]
        os = splitVersion(platform[0])
        return {'browser': browser, 'os': os, 'device': device}
    
    if platform[0].startswith('Symbian'):
        browser = parseWebKitTail(info)
        device = platform[1].split()[-1].split('/')[0]
        os = splitVersion(platform[0])
        return {'browser': browser, 'os': os, 'device': device}

    if platform[0] == 'X11':
        if platform[1] == 'U':
            platform.pop(1)
        osname = platform[1].split()[0]
        if osname == 'Linux':
            # TODO architecture
            browser = parseWebKitTail(info)
            return {'browser': browser, 'os': (osname, [])}
        elif osname == 'CrOS':
            osver = version(platform[1].split()[-1])
            browser = parseWebKitTail(info)
            return {'browser': browser, 'os': (osname, osver)}

    return# info
    #return platform, info

def parseWebKitTail(info):
    browser_name = None
    browser_version = None
    if len(info) < 2:
        return # unknown
    applewebkit = info.pop(0) # different versions
    khtml = info.pop(0)
    if not applewebkit.startswith('AppleWebKit/') or khtml != '(KHTML, like Gecko)':
        return
    if len(info) == 1:
        return splitVersion(info[0])
    fb = parseFacebookUAString(info[-1])
    if fb is not None:
        browser_version = version(fb['AV'])
        # different devices
        app_name = fb.get('AN')
        if app_name == 'MessengerForiOS':
            browser_name = 'Facebook Messenger'
        elif app_name == 'FBIOS':
            browser_name = 'Facebook App' # iOS
        else:
            if fb.get('_IAB') == 'FB4A':
                browser_name = 'Facebook App' # Android
            else:
                browser_name = 'Facebook (?)'
        return browser_name, browser_version

    # TODO: this function should probably know something about the operating system...
    
    priority = ['Mobile', 'Safari', 'Chrome', 'Version']
    browser = None
    best_priority = -1
    for i in info:
        name, ver = splitVersion(i)
        if not name in priority:
            best_priority = len(priority) 
            browser = (name, ver)
            if ver:
                break
        elif priority.index(name) > best_priority:
            browser = (name, ver)
            best_priority = priority.index(name)
    
    return browser

def parseFacebookUAString(fbstr):
    if fbstr[0] != '[' or fbstr[-1] != ']':
        return
    fbstr = fbstr[1:-1].strip(';')
    dictionary = {}
    for pair in fbstr.split(';'):
        pair = pair.strip(' ')
        if not pair.startswith('FB'):
            return
        if pair.count('/') != 1:
            return
        key, value = pair.split('/')
        dictionary.update({key[2:]: value})
    return dictionary

def splitUserAgent(string):
    # "foo (bar foo) bar" -> ["foo", "(bar foo)", "bar"]
    return re.findall(r'(\([^()]+\)|\[[^\[\]]+\]|[^ ()]+)', string)

def splitVersion(string):
    if not '/' in string:
        return string, []
    #name, ver = string.split('/') # not tested
    name = string.split('/')[0]
    ver = string.split('/')[1]
    return name, version(ver)

def version(version):
    version = re.match(r'[0-9_.]*', version).group(0)
    if not version:
        return None
    #version = version.split('-')[0] # Google-HTTP-Java-Client/1.17.0-rc
    numbers = re.split(r'_|\.', version)
    return [int(x) for x in numbers]

if __name__ == '__main__':

    uafile = '/dev/stdin'

    for line in open(uafile):
        ua = line.strip('\n')
        parsed = parseUserAgent(ua)
        #print(repr(ua))
        if parsed is not None:
            print(parsed)
            0
        else:
            #print(ua)
            0
        #if parsed is not None:
            #print(parsed)
        #if parsed:
            #print(ua)
       #     print(parsed)
            #print()
