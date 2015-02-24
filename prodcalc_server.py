from flask import Flask
from flask import render_template
import profitcalc

app = Flask(__name__)

@app.route('/')
def index():
  return "EVE Production Calcs - Under Construction, Check Back Soon!"

@app.route('/<int:type_id>')

def process_item_by_id(type_id):
  name = profitcalc.get_name_by_id(type_id)
  prodcost = profitcalc.get_prod_cost_by_id(type_id)
  value = profitcalc.get_price(type_id)
  profit = value - prodcost
  time = profitcalc.get_build_time_by_id(type_id)
  profit_per_hour = profit / time * 60 * 60 if time > 0 else 0
  #Inefficient for now - already called as part of get_prod_cost_by_id, decouple later
  materials = profitcalc.get_item_materials_rec(type_id)
  material_ids = profitcalc.unpack_material_typeids(materials)
  prices = profitcalc.get_prices(material_ids)
  item_attrs = {
    'name': name,
    'prodcost': prodcost,
    'value': value,
    'profit': profit,
    'time': time,
    'profit_per_hour': profit_per_hour,
    'materials': materials, 
    'prices': prices,
  }
  return item_attrs

#Deprecated in favor of show_item_by_id_rec
#def show_item_by_id(type_id):
#  item_attrs = process_item_by_id(type_id)
#  return render_template('item.html', **item_attrs)

def show_item_by_id_rec(type_id):
  item_attrs = process_item_by_id(type_id)
  #Template is only fake-recursive for now.  Will need extensive reformatting.
  submaterials = {}
  submat_totals = {}

  #Preprocess total cost of submaterials for the template
  for mat_id, mat_attrs in item_attrs['materials'].iteritems():
    submaterials[mat_id] = []
    submat_totals[mat_id] = 0
    for sub_id, sub_attrs in mat_attrs[2].iteritems():
      submaterials[mat_id].append((sub_id, sub_attrs,))
      submat_totals[mat_id] += sub_attrs[0] * item_attrs['prices'][sub_id] * mat_attrs[0]

  prodcost_scratch = sum(submat_totals.values())
  return render_template('item_rec.html', 
    submaterials = submaterials, 
    submat_totals = submat_totals,
    prodcost_scratch = prodcost_scratch,
    **item_attrs
  )

@app.route('/<item_name>')
def show_item_by_name_rec(item_name):
  #A bit wasteful, since it'll do an extra lookup to find the name again
  #Still doing it this way for now to ensure code consistency rather than duplication
  type_id = profitcalc.get_type_id_by_name(item_name)
  return show_item_by_id_rec(type_id)

#Deprecated in favor of show_item_by_name_rec
#def show_item_by_name(item_name):
#  type_id = profitcalc.get_type_id_by_name(item_name)
#  return show_item_by_id(type_id)

@app.route('/favicon.ico')
def favicon():
  #favicon browser autoquery tries to trigger name-recognition without this
  return ""

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=False)
