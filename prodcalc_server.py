from flask import Flask
from flask import render_template
import profitcalc

app = Flask(__name__)

@app.route('/')
def index():
  return "EVE Production Calcs - Under Construction, Check Back Soon!"

@app.route('/<int:typeID>')
def show_item_by_id(typeID):
  name = profitcalc.get_name_by_id(typeID)
  prodcost = profitcalc.get_prod_cost_by_id(typeID)
  value = profitcalc.get_item_value(typeID)
  profit = value - prodcost
  return render_template('item.html', name = name, prodcost = prodcost, value = value, profit = profit)

@app.route('/<itemName>')
def show_item_by_name(itemName):
  #A bit wasteful, since it'll do an extra lookup to find the name again
  #Still doing it this way for now to ensure code consistency rather than duplication
  typeID = profitcalc.get_typeid_by_name(itemName)
  return show_item_by_id(typeID)

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=False)
