import pinoywok.helpers
#import json
from jinja2 import Template
from pinoywok.helpers import get_json_value

def html_template(templates,id,provider,data,order):
    filename = f"{templates}/jumpseller_order.html"
    html = pinoywok.helpers.read_file(filename)
    template = Template(html)

    #products = data['order']['products']
    products = get_json_value(order,"order.products")
    total = get_json_value(order,"order.total")
    subtotal = get_json_value(order,"order.subtotal")
    shipping_required = get_json_value(order,"order.shipping_required")
    shipping = get_json_value(order,"order.shipping")
    orderno = get_json_value(order,"order.id")
   
    rendered_html = template.render(orderno=orderno,id=id,provider=provider,products=products,total=total,subtotal=subtotal,shipping_required=shipping_required,shipping=shipping)
    return rendered_html
    
def notification_message(data,order):
    products = get_json_value(order,"order.products")
    print("DATA")
    print(data)
    notification = ""
    for product in products:
        notification += str(product['qty'])+", repito, "+str(product['qty'])+" "+product['name']+" ,"
    return notification
