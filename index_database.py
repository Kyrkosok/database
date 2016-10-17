#!/usr/bin/env
import pywikibot, sqlite3, re, sys, requests, time
from pywikibot import pagegenerators
from ksamsok import KSamsok

class Database:
    def __init__(self):
        # load query files
        with open('churches.rq', 'r') as sparql_file:
            # remove comments and line-breaks
            self.sparql = re.sub(r'(#(()|(.+))\n)|(\n)', '', sparql_file.read())

        with open('create_table.sql', 'r') as sql_table_file:
            self.table_sql = sql_table_file.read()

        # create and connect to db
        self.db_connection = sqlite3.connect('db.sqlite')
        self.c = self.db_connection.cursor()
        # create table
        self.c.execute(self.table_sql)
        self.db_connection.commit()
        
        # fetch data and build database
        self.index()
        
        # close database connection
        self.db_connection.close()

    def index(self):
        # setup pywikibot and initialize generator
        pywikibot.handle_args(sys.argv[1:])
        site = pywikibot.Site()
        generator = pagegenerators.WikidataSPARQLPageGenerator(self.sparql, site)
        
        # setup instance of the KSamsok class
        # the api key is never used so no need to use another one
        soch = KSamsok('test')
        
        for i in generator:
            item = i.get()
            data = {}
            
            # get the raw wikidata uri without Q
            data['wikidata'] = re.sub(r'(?!\d).', '', str(i))
            
            # make sure the item does not exist in our database
            if not self.primary_key_exists(data['wikidata']):
                # parse the kulturarvsdata uri or set to false if invalid
                data['kulturarvsdata'] = soch.formatUri(item['claims']['P1260'][0].getTarget(), 'raw', True)
                #TODO make a log of items with broken kulturarvsdata uris
                if data['kulturarvsdata']:
                    # fetch stuff from the wikidata item
                    data['wikipedia'] = item['sitelinks']['svwiki']

                    try:
                        data['commons'] = item['claims']['P373'][0].getTarget()
                    except(KeyError):
                        data['commons'] = ''

                    try:
                        data['image'] = re.sub(r'\]\]', '', re.sub(r'\[\[commons:', '', str(item['claims']['P18'][0].getTarget())))
                    except(KeyError):
                        data['image'] = ''

                    coord_pair = item['claims']['P625'][0].getTarget()
                    data['lat'] = coord_pair.lat
                    data['lon'] = coord_pair.lon
                    
                    data['label'] = item['labels']['sv']
                    
                    # fetch stuff from kulturarvsdata
                    record = soch.getObject(data['kulturarvsdata'])

                    if record['presentation']['description']:
                        # if the string is too short to be useful drop it
                        if len(record['presentation']['description']) > 30:
                            data['description'] = record['presentation']['description']
                        else:
                            data['description'] = ''
                    else:
                        data['description'] = ''
                    
                    # fetch intro paragraphs from wikipedia
                    #TODO if the connection to wikipedia fails then 
                    # the item should be dropped(may need to be refactored)
                    try:
                        r = requests.get('https://sv.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exintro=&explaintext=&titles=' + data['wikipedia'])
                        result = r.json()

                        # the page id is the unknown key the loop is for figuring it out
                        # dictionaries does not support indexing as they are unsorted...
                        for key in result['query']['pages']:
                            data['wp_description'] = result['query']['pages'][key]['extract']
                    except(KeyError):
                        data['wp_description'] = ''
                    
                    try:
                        if (data['image'] != ''):
                            r = requests.get('https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=pageimages&piprop=thumbnail|name|original&pithumbsize=110&titles=File:' + data['image'])
                            result = r.json()
                            
                            for key in result['query']['pages']:
                                data['image_thumbnail'] = result['query']['pages'][key]['thumbnail']['source']
                                data['image_original'] = result['query']['pages'][key]['thumbnail']['original']
                        else:
                            data['image_thumbnail'] = ''
                            data['image_original'] = ''
                    except(KeyError):
                        data['image_thumbnail'] = ''
                        data['image_original'] = ''
                    
                    # write and commit church to db
                    self.c.execute('''INSERT INTO `churches` (
                                        `wikidata`,
                                        `label`,
                                        `kulturarvsdata`,
                                        `description`,
                                        `lat`,
                                        `lon`,
                                        `wikipedia`,
                                        `wp_description`,
                                        `commons`,
                                        `image`,
                                        `image_thumbnail`,
                                        `image_original`
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                  (data['wikidata'],
                                   data['label'],
                                   data['kulturarvsdata'],
                                   data['description'],
                                   data['lat'],
                                   data['lon'],
                                   data['wikipedia'],
                                   data['wp_description'],
                                   data['commons'],
                                   data['image'],
                                   data['image_thumbnail'],
                                   data['image_original']))
                    self.db_connection.commit()

    def primary_key_exists(self, key):
        self.c.execute('SELECT `wikidata` FROM `churches` WHERE `wikidata` = ' + key)
        
        if self.c.fetchone():
            return True
        else:
            return False

t0 = time.time()
database = Database()
t1 = time.time()
print('Done! in ' + str((t1 - t0) / 60) + ' minutes')