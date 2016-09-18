# -*- coding: utf-8 -*-
from openerp import http
from datetime import datetime

class IOT(http.Controller):

    @http.route('/iot', auth='public')
    def iot(self, **post):
        nhiet_do    = post.get('nhiet_do', False)
        anh_sang    = post.get('anh_sang', False)
        do_am       = post.get('do_am', False)
        http.request.env['thongke'].sudo().create({
            'name': str(datetime.now()),
            'nhiet_do': nhiet_do,
            'anh_sang': anh_sang,
            'do_am': do_am,
        })