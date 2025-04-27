import pinoywok.helpers

def htmlTemplate():
    filename = "templates/default_order.html"
    text = pinoywok.helpers.read_file(filename)
    return text
    