# Copyright 2018 Luis M. Ontalba <luismaront@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models
#from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx

class details_taxes_xlsx(models.AbstractModel):
    _name = 'details.taxes.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        book = objects[0]
        bold = workbook.add_format({'bold': True})

        def fill_table(sheet_name, lines, estructure_lines=False):
            sheet = workbook.add_worksheet(sheet_name[:31])
            row = col = 0
            xlsx_header = [
                _('Invoice'),
                _('Type'),
                _('Date'),
                _('Partner'),
                _('VAT'),
                _('Base'),
                _('Tax'),
                _('Base Refund'),
                _('Tax Refund'),
                _('Base Total'),
                _('Tax Total'),
                _('TOTAL'),
            ]
            #if estructure_lines:
            #    xlsx_header.insert(0, _('Reference'))
            for col_header in xlsx_header:
                sheet.write(row, col, col_header, bold)
                col += 1
            row = 1
            for line in lines:
                col = 0
                sheet.write(row, col, line.ref)
                col += 1
                sheet.write(row, col, line.type)
                col += 1
                sheet.write(row, col, line.invoice_date)
                col += 1
                sheet.write(row, col, line.partner_id.name)
                col += 1
                sheet.write(row, col, line.vat_number)
                col += 1
                sheet.write(row, col, line.tax_id.name)
                col += 1
                sheet.write(row, col, line.amount_untaxed)
                col += 1
                sheet.write(row, col, line.amount_tax)
                col += 1
                sheet.write(row, col, line.amount_refund_untaxed)
                col += 1
                sheet.write(row, col, line.amount_refund_tax)
                col += 1
                sheet.write(row, col, line.amount_total_untaxed)
                col += 1
                sheet.write(row, col, tax_line.amount_total_tax)
                row += 1

        if book.estructure_tax_line_ids:
            report_name = _('')
            lines = book.estructure_tax_line_ids
            fill_table(report_name, lines)
        """if book.rectification_issued_line_ids:
            report_name = _('Issued Refund Invoices')
            lines = book.rectification_issued_line_ids
            fill_table(report_name, lines)
        if book.received_line_ids:
            report_name = _('Received Invoices')
            lines = book.received_line_ids
            fill_table(report_name, lines, received_lines=True)
        if book.rectification_received_line_ids:
            report_name = _('Received Refund Invoices')
            lines = book.rectification_received_line_ids
            fill_table(report_name, lines, received_lines=True)"""
