import hashlib,json,re,time
from datetime import datetime,timedelta,timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

SOURCE='https://www.visitcos.com/events/free-events/'
HEADERS={'User-Agent':'GuardianReset event-feed updater (GitHub Actions; local Colorado Springs events)'}
CATS=['Live Music','Arts & Culture','Outdoors & Hiking','Festivals & Markets','Gaming','Movies','Classes & Workshops','Sports & Recreation','Community','Volunteer','Museums & Attractions','Other']

def category(title,desc):
    x=(title+' '+desc).lower()
    if any(k in x for k in ['concert','music','band','open mic','choir','song']): return 'Live Music'
    if any(k in x for k in ['hike','trail','park','outdoor','nature','forest','owl','garden of the gods']): return 'Outdoors & Hiking'
    if any(k in x for k in ['market','festival','fair','craft fair','harvest']): return 'Festivals & Markets'
    if any(k in x for k in ['museum','tour','exhibit','historic']): return 'Museums & Attractions'
    if any(k in x for k in ['movie','film','cinema']): return 'Movies'
    if any(k in x for k in ['workshop','class','lesson','writing']): return 'Classes & Workshops'
    if any(k in x for k in ['soccer','basketball','sport','race','run']): return 'Sports & Recreation'
    if any(k in x for k in ['volunteer','cleanup','clean-up','stewardship']): return 'Volunteer'
    if any(k in x for k in ['art','dance','theater','theatre','poetry']): return 'Arts & Culture'
    return 'Community'

def text(v):
    return re.sub(r'\s+',' ',v or '').strip()

def parse_jsonld(soup):
    for tag in soup.find_all('script',type='application/ld+json'):
        try:
            data=json.loads(tag.string or tag.get_text())
        except Exception: continue
        stack=data if isinstance(data,list) else [data]
        for obj in stack:
            if isinstance(obj,dict) and ('Event' in obj.get('@type',[]) if isinstance(obj.get('@type'),list) else obj.get('@type')=='Event'):
                return obj
    return {}

def parse_event(url):
    r=requests.get(url,headers=HEADERS,timeout=25); r.raise_for_status(); soup=BeautifulSoup(r.text,'html.parser'); obj=parse_jsonld(soup)
    title=text(obj.get('name')) or text(soup.find('h1').get_text(' ',strip=True) if soup.find('h1') else '')
    start=obj.get('startDate','')
    if not title or not start: return None
    try: dt=datetime.fromisoformat(start.replace('Z','+00:00'))
    except Exception: return None
    loc=obj.get('location') or {}; addr=loc.get('address') or {}; address=', '.join(x for x in [addr.get('streetAddress'),addr.get('addressLocality'),addr.get('addressRegion'),addr.get('postalCode')] if x)
    offers=obj.get('offers') or {}; offer_text=json.dumps(offers).lower(); free=('free' in offer_text or '"price":"0"' in offer_text or '"price":0' in offer_text)
    desc=text(obj.get('description'))
    return {'id':hashlib.sha1((url+start).encode()).hexdigest()[:12],'title':title,'date':dt.astimezone().strftime('%Y-%m-%d'),'time':dt.astimezone().strftime('%-I:%M %p'),'cat':category(title,desc),'free':free,'place':text(loc.get('name')),'address':address,'source':'Visit Colorado Springs','url':url,'desc':desc[:500]}

def geocode(e):
    if not e.get('address'): return
    q=e['address']+', Colorado'
    r=requests.get('https://nominatim.openstreetmap.org/search',params={'q':q,'format':'json','limit':1},headers=HEADERS,timeout=20)
    data=r.json()
    if data: e['lat']=float(data[0]['lat']); e['lng']=float(data[0]['lon'])

def main():
    soup=BeautifulSoup(requests.get(SOURCE,headers=HEADERS,timeout=30).text,'html.parser')
    urls=[]
    for a in soup.select('a[href]'):
        href=urljoin(SOURCE,a.get('href'))
        if '/events/' in href and href.rstrip('/')!=SOURCE.rstrip('/') and href not in urls: urls.append(href)
    now=datetime.now(timezone.utc); cutoff=now+timedelta(days=8); out=[]
    for url in urls[:80]:
        try:
            e=parse_event(url)
            if not e or not e['free']: continue
            dt=datetime.fromisoformat(e['date']+'T00:00:00+00:00')
            if now-timedelta(days=1)<=dt<=cutoff:
                geocode(e); out.append(e); time.sleep(1.1)
        except Exception: continue
    out=[e for e in out if 'lat' in e and 'lng' in e]
    out.sort(key=lambda e:(e['date'],e['time'],e['title']))
    payload={'meta':{'updatedAt':datetime.now(timezone.utc).isoformat(),'source':'Visit Colorado Springs free-events calendar','windowDays':8},'events':out}
    with open('events.json','w') as f: json.dump(payload,f,indent=2,ensure_ascii=False)
    print(f'Wrote {len(out)} free events')
if __name__=='__main__': main()
