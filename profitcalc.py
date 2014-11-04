import evelink.api
import evelink.thirdparty.eve_central as evelink_evec
import urllib2
import psycopg2

#EVE-Central API setup
api = evelink.api.API()
eve = evelink.eve.EVE()
JITA = 30000142
def fetch_func(url):
  return urllib2.urlopen(url).read()
evec = evelink_evec.EVECentral(url_fetch_func = fetch_func)
#Duct-tape caching solution to not make EVE-Central cry while debugging
CACHED_PRICES = {}

#PsycoPG/PostgreSQL setup
conn = psycopg2.connect("dbname=EVE_Bulk user=cheezy52")
cur = conn.cursor()

def get_type_id_by_name(item_name):
  #Returns the typeID for a single item name.  Must be an exact match.
  cur.execute('SELECT "typeID" FROM "invTypes" WHERE "typeName" = (%s);', [item_name])
  return cur.fetchone()[0]

def get_name_by_id(type_id):
  #Returns the item name for a single typeID.
  cur.execute('SELECT "typeName" FROM "invTypes" WHERE "typeID" = (%s);', [type_id])
  return cur.fetchone()[0]

def get_item_materials(type_id):
  #Returns the materials required to construct an item, given the output item's typeID.
  #Outputs are returned as a dict.  Keys: material typeIDs.  Values: (quantity, name).
  cur.execute('SELECT iam."materialTypeID", iam."quantity", it."typeName" FROM "industryActivityProducts" iap JOIN "industryActivityMaterials" iam ON iap."typeID" = iam."typeID" AND iam."activityID" = 1 JOIN "invTypes" it ON iam."materialTypeID" = it."typeID" WHERE "productTypeID" = (%s);', [type_id])
  materials = {}
  for record in cur:
    materials[record[0]] = (record[1], record[2])
  return materials

def get_item_values(type_ids):
  #Returns the current market values for all typeIDs in the input array.
  #Outputs are returned as a dict.  Keys: material typeIDs.  Values: market avg. price.
  prices = {}
  if all (type_id in CACHED_PRICES.keys() for type_id in type_ids):
    #Cache hit
    for type_id in type_ids:
      prices[type_id] = CACHED_PRICES[type_id]
    return prices
  else:
    #Cache miss
    response = evec.market_stats(type_ids, system=JITA)
    print "EVE Central query fired"
    for type_id in response.keys():
      prices[type_id] = response[type_id]['sell']['percentile']
      CACHED_PRICES[type_id] = prices[type_id]
    return prices

def get_item_value(type_id):
  #Convenience wrapper for returning a single item's value.
  #Returns the value directly, not as a dict.
  if type_id in CACHED_PRICES.keys():
    #Cache hit
    return CACHED_PRICES[type_id]
  else:
    #Cache miss
    value = get_item_values([type_id])[type_id]
    CACHED_PRICES[type_id] = value
    return value

def get_prod_cost_by_name(item_name):
  #Convenience wrapper for get_prod_cost_by_id
  type_id = get_type_id_by_name(item_name)
  return get_prod_cost_by_id(type_id)

def get_prod_cost_by_id(type_id):
  #Returns the cost to produce a given item from minerals.
  #Use sparingly - initial implementation, NO caching of API results yet!
  materials = get_item_materials(type_id)
  prices = get_item_values(materials.keys())
  prodcost = 0
  for mat in materials.keys():
    prodcost += materials[mat][0]*prices[mat]
  return prodcost

def get_prod_profit_by_name(item_name):
  #Returns the gross profit given by producing an item over its current market value.
  type_id = get_type_id_by_name(item_name)
  return get_item_value(type_id) - get_prod_cost_by_id(type_id)