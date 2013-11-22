from bcdoc.restdoc import ReSTDocument

from botocore import xform_name


def to_snake_case(camel_case_name):
    """
    Converts CamelCaseNames to snake_cased_names.

    :param camel_case_name: The name you'd like to convert from.
    :type camel_case_name: string

    :returns: A converted string
    :rtype: string
    """
    return xform_name(camel_case_name)


def to_camel_case(snake_case_name):
    """
    Converts snake_cased_names to CamelCaseNames.

    :param snake_case_name: The name you'd like to convert from.
    :type snake_case_name: string

    :returns: A converted string
    :rtype: string
    """
    bits = snake_case_name.split('_')
    return ''.join([bit.capitalize() for bit in bits])


def html_to_rst(html):
    """
    Converts the service HTML docs to reStructured Text, for use in docstrings.

    :param html: The raw HTML to convert
    :type html: string

    :returns: A reStructured Text formatted version of the text
    :rtype: string
    """
    doc = ReSTDocument()
    doc.include_doc_string(html)
    raw_doc = doc.getvalue()
    return raw_doc.decode('utf-8')
