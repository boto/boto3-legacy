from botocore import xform_name


def to_snake_case(camel_case_name):
    return xform_name(camel_case_name)


def to_camel_case(snake_case_name):
    bits = snake_case_name.split('_')
    return ''.join([bit.capitalize() for bit in bits])


def html_to_rst(html):
    # FIXME: Need to actually do some conversion!
    return html
