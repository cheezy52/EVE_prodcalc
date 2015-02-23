import evelink.api
import evelink.thirdparty.eve_central as evelink_evec
import urllib2
import psycopg2
import datetime

#EVE-Central API setup
api = evelink.api.API()
eve = evelink.eve.EVE()
JITA = 30000142
def fetch_func(url):
  return urllib2.urlopen(url).read()
evec = evelink_evec.EVECentral(url_fetch_func = fetch_func)
CACHE_DUR = datetime.timedelta(days=1)

#PsycoPG/PostgreSQL setup
conn = psycopg2.connect("dbname=EVE_Bulk user=cheezy52")
cur = conn.cursor()

def get_type_id_by_name(item_name):
  """Returns the typeID for a single item name.  Must be an exact match."""

  cur.execute("""
    SELECT "typeID" 
    FROM "invTypes" 
    WHERE "typeName" = (%s);""", 
    [item_name])
  return cur.fetchone()[0]

def get_name_by_id(type_id):
  """Returns the item name for a single typeID."""

  cur.execute("""
    SELECT "typeName" 
    FROM "invTypes" 
    WHERE "typeID" = (%s);""", 
    [type_id])
  return cur.fetchone()[0]

def get_item_materials(type_id):
  """Returns the materials needed to build a single item.

  Input: type_id
  Output: {type_id: (quantity, name)}"""
  #NEEDS UPDATE TO HANDLE JOBS THAT OUTPUT MORE THAN ONE ITEM/RUN

  cur.execute("""
    SELECT iam."materialTypeID", iam."quantity", it."typeName" 
    FROM "industryActivityProducts" iap 
    JOIN "industryActivityMaterials" iam 
    ON iap."typeID" = iam."typeID" 
    AND iam."activityID" = 1 
    JOIN "invTypes" it 
    ON iam."materialTypeID" = it."typeID" 
    WHERE "productTypeID" = (%s);""", 
    [type_id])
  materials = {}
  for record in cur:
    materials[record[0]] = (record[1], record[2])
  return materials

def get_item_materials_rec(type_id):
  """Returns the materials needed to build a single item.
  Also returns the materials needed to build those materials recursively.

  Input: type_id
  Output: {type_id: (quantity, name, {submaterials})}"""

  materials = get_item_materials(type_id)
  new_materials = {}

  for mat_typeid, mat_attrs in materials.iteritems():
    new_mat_attrs = mat_attrs + (get_item_materials_rec(mat_typeid),)
    new_materials[mat_typeid] = new_mat_attrs
  return new_materials

def get_prices(type_ids, cache_dur = CACHE_DUR):
  """Returns the prices for the input type IDs.

  Arguments:
  type_ids: An array of type IDs for which to check prices
  cache_dur: The maximum interval by which prices can be outdated

  Output: {type_id: price}

  First attempts to check database for fresh entries.
  Any stale entries will have fresh data retrieved from EVE Central,
  then call the get_prices function again with fresh data available."""

  try:
    dt = datetime.datetime.now() - cache_dur
    cur.execute("""
      SELECT "typeID", "price", "timeUpdated"
      FROM "invTypePrices"
      WHERE "typeID" = ANY (%s)
      AND "timeUpdated" > (%s);""",
      [list(type_ids), dt])
  
    prices = {}
    for record in cur:
      prices[record[0]] = record[1]

    if len(prices.keys()) == len(type_ids):
      #All records were found with up-to-date info and returned
      return prices
  
    else:
      #At least one outdated or nonexistent record
      prices_to_update = []
      for type_id in type_ids:
        if not type_id in prices.keys():
          prices_to_update.append(type_id)
      update_prices(prices_to_update)
    
      #call ourselves again with updated record - verifies properly persisted
      #danger of infinite loop if persisting fails!
      return get_prices(type_ids)

  except psycopg2.ProgrammingError as e:
    print e
    print "Error fetching item prices.  Price table not created?"
    conn.rollback()
    create_price_table()

def update_prices(type_ids, system=JITA):
  """Polls EVE Central for item prices, and saves them to the database.

  Arguments:
  type_ids: An array of type IDs for which to update prices
  system: The EVE solar system in which to retrieve prices (numeric)

  No outputs - function purely updates database entries."""

  dt = datetime.datetime.now()
  print "Firing EVE Central query..."
  response = evec.market_stats(type_ids, system=system)
  for type_id in response.keys():
    print "Updating price on " + str(type_id)
    cur.execute("""
      UPDATE "invTypePrices"
      SET "price" = (%s), "timeUpdated" = (%s)
      WHERE "typeID" = (%s);""",
      [response[type_id]['sell']['percentile'], dt, type_id])
  
  print "Finalizing transaction..."
  conn.commit()

def get_price(type_id):
  """Convenience wrapper.  Returns a single item's price directly (no dict)."""

  return get_prices([type_id])[type_id]

def get_prod_cost_by_name(item_name):
  """Convenience wrapper for get_prod_cost_by_id using an item's name."""

  type_id = get_type_id_by_name(item_name)
  return get_prod_cost_by_id(type_id)

def get_prod_cost_by_id(type_id):
  """Returns the cost to produce a given item from minerals."""

  materials = get_item_materials(type_id)
  prices = get_prices(materials.keys())
  prodcost = 0
  for mat in materials.keys():
    prodcost += materials[mat][0]*prices[mat]
  return prodcost

def get_prod_profit_by_name(item_name):
  """Returns the profit given by producing an item relative to its market value."""
  type_id = get_type_id_by_name(item_name)
  return get_price(type_id) - get_prod_cost_by_id(type_id)

def get_build_time_by_id(type_id):
  """Returns the time, in seconds, required to build an item (without modifiers)."""
  cur.execute("""
    SELECT "time" 
    FROM "industryActivity" ia
    JOIN "industryActivityProducts" iap
    ON ia."typeID" = iap."typeID"
    WHERE iap."productTypeID" = (%s)
    AND ia."activityID" = 1;""",
    [type_id])
  output = cur.fetchone()
  return output[0] if output else 0

def create_price_table():
  """Adds the table for price data to the database.

  Should only be necessary after EVE expansions, and the accompanying
  new version of the database."""

  try:
    print "Creating table"
    cur.execute("""
      CREATE TABLE "invTypePrices" 
      ("typeID" integer PRIMARY KEY,
      "price" integer,
      "timeUpdated" timestamp);""")
    
    print "Fetching existing typeIDs"
    cur.execute("""
      SELECT "typeID"
      FROM "invTypes";""")
    
    print "Creating records"
    type_ids = cur.fetchall()
    cur.executemany("""
      INSERT INTO "invTypePrices" ("typeID")
      VALUES (%s);""",
      (type_ids))
    
    print "Populating records"
    long_long_ago = datetime.datetime.min
    cur.execute("""
      UPDATE "invTypePrices"
      SET "price" = (%s), "timeUpdated" = (%s);""",
      (0, long_long_ago))

    print "Finalizing transaction..."
    conn.commit()
  
  except Exception as e:
    print e
    conn.rollback()

def unpack_material_typeids(materials):
  """Unpacks a list of materials with submaterials from get_item_materials_rec.
  Traverses the nested dictionaries and returns a set of all seen typeids.

  Input: dict of materials, from get_item_materials_rec
  Output: [type_ids]"""

  type_ids = set([])
  for mat_typeid, mat_attrs in materials.iteritems():
    type_ids.add(mat_typeid)
    type_ids |= unpack_material_typeids(mat_attrs[2])

  return type_ids