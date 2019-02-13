# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero, pycompat
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError, ValidationError

import time
import math


class AccountBankStatementLine(models.Model):
  _inherit = 'account.bank.statement.line'

  #@api.multi
  def fast_counterpart_creation(self):
        for st_line in self:
            # Technical functionality to automatically reconcile by creating a new move line
            vals = {
                'name': st_line.name,
                'debit': st_line.amount < 0 and -st_line.amount or 0.0,
                'credit': st_line.amount > 0 and st_line.amount or 0.0,
                'account_id': st_line.account_id.id,
            }
            #st_line.process_reconciliation(new_aml_dicts=[vals])

