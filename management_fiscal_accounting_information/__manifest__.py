# See README.rst file on addon root folder for license details

{
    "name": "Información fiscal y contable",
    "version": "11.0.2.1.0",
    "author": "Infobit Informatica",
    "category": "Accounting",    
    "depends": [
        'account',
        'report_xlsx',
        'proforma_in_invoice',
    ],
    'description': """
    Se incorporar una opción para generar los siguientes datos:

       - El resumen de impuestos

       - El detalle de impuestos
    """,
    'data': [
        'views/estructure_tax_line.xml',
        'views/management_fiscal_accounting_information.xml',
        'views/type_taxes_information.xml',
        #'views/account_tax_group.xml',
        'views/account_tax.xml',
        'report/management_fiscal_accounting_information_xlsx.xml',
    ],
    "installable": True,
}
