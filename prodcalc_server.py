from flask import Flask
from flask import render_template
import profitcalc

app = Flask(__name__)

@app.route('/')
def index():
  return "EVE Production Calcs - Under Construction, Check Back Soon!"

@app.route('/<int:type_id>')
def show_item_by_id(type_id):
  name = profitcalc.get_name_by_id(type_id)
  prodcost = profitcalc.get_prod_cost_by_id(type_id)
  value = profitcalc.get_item_value(type_id)
  #Inefficient for now - already called as part of get_prod_cost_by_id, decouple later
  materials = profitcalc.get_item_materials(type_id)
  profit = value - prodcost
  return render_template(
    'item.html', name = name, prodcost = prodcost, 
    value = value, profit = profit, materials = materials,
    #absolute overkill here, interim solution only
    prices = profitcalc.CACHED_PRICES)

@app.route('/<item_name>')
def show_item_by_name(item_name):
  #A bit wasteful, since it'll do an extra lookup to find the name again
  #Still doing it this way for now to ensure code consistency rather than duplication
  type_id = profitcalc.get_type_id_by_name(item_name)
  return show_item_by_id(type_id)

@app.route('/favicon.ico')
def favicon():
  #favicon browser autoquery tries to trigger name-recognition without this
  return ""

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
