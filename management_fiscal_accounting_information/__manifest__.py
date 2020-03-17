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

       - El resumen de ivas
       - El detalle de ivas
       - Libro contable resumen por grupos de cuentas
       - Libro contable detallado
       - Detalle de impuestos (Para sacar retenciones, ...)
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data_type_taxes_information.xml',
        'views/estructure_tax_line.xml',
        'views/management_fiscal_accounting_information.xml',
        'views/type_taxes_information.xml',
        'views/account_tax.xml',
        'report/management_fiscal_accounting_information_xlsx.xml',
        'report/report_management_fiscal_information.xml',
    ],
    "installable": True,
}
