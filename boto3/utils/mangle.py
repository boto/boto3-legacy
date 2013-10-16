from botocore import xform_name


def to_snake_case(camel_case_name):
    # FIXME: Revisit this to make sure we're safe with the above import
    #        and that we'd really prefer that behavior.
    # bits = []
    #
    # for char in camel_case_name:
    #     if char.isupper():
    #         bits.append('_')
    #
    #     bits.append(char.lower())
    #
    # return ''.join(bits).lstrip('_')
    return xform_name(camel_case_name)


def to_camel_case(snake_case_name):
    bits = snake_case_name.split('_')
    return ''.join([bit.capitalize() for bit in bits])


def html_to_rst(html):
    # FIXME: Need to actually do some conversion!
    return html
