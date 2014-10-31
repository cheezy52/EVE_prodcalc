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

#PsycoPG/PostgreSQL setup
conn = psycopg2.connect("dbname=EVE_Bulk user=cheezy52")
cur = conn.cursor()

def get_typeid_by_name(item_name):
  #Returns the typeID for a single item name.  Must be an exact match.
  cur.execute('SELECT "typeID" FROM "invTypes" WHERE "typeName" = (%s);', [item_name])
  return cur.fetchone()[0]

def get_name_by_id(type_id):
  #Returns the item name for a single typeID.
  cur.execute('SELECT "typeName" FROM "invTypes" WHERE "typeID" = (%s);', [type_id])
  return cur.fetchone()[0]

def get_item_materials(type_id):
  #Returns the materials required to construct an item, given the output item's typeID.
  #Outputs are returned as a dict.  Keys: material typeIDs.  Values: quantity.
  cur.execute('SELECT iam."materialTypeID", iam."quantity" FROM "industryActivityProducts" iap JOIN "industryActivityMaterials" iam ON iap."typeID" = iam."typeID" AND iam."activityID" = 1 JOIN "invTypes" it ON iam."materialTypeID" = it."typeID" WHERE "productTypeID" = (%s);', [type_id])
  materials = {}
  for record in cur:
    materials[record[0]] = record[1]
  return materials

def get_item_values(type_ids):
  #Returns the current market values for all typeIDs in the input array.
  #Outputs are returned as a dict.  Keys: material typeIDs.  Values: market avg. price.
  response = evec.market_stats(type_ids, system=JITA)
  prices = {}
  for key in response.keys():
    prices[key] = response[key]['sell']['percentile']
  return prices

def get_item_value(type_id):
  #Convenience wrapper for returning a single item's value.
  #Returns the value directly, not as a dict.
  return get_item_values([type_id])[type_id]

def get_prod_cost_by_name(item_name):
  #Convenience wrapper for get_prod_cost_by_id
  typeID = get_typeid_by_name(item_name)
  return get_prod_cost_by_id(typeID)

def get_prod_cost_by_id(type_id):
  #Returns the cost to produce a given item from minerals.
  #Use sparingly - initial implementation, NO caching of API results yet!
  materials = get_item_materials(type_id)
  prices = get_item_values(materials.keys())
  prodcost = 0
  for mat in materials.keys():
    prodcost += materials[mat]*prices[mat]
  return prodcost

def get_prod_profit_by_name(item_name):
  #Returns the gross profit given by producing an item over its current market value.
  typeID = get_typeid_by_name(item_name)
  return get_item_value(typeID) - get_prod_cost_by_id(typeID)