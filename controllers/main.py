# -*- coding: utf-8 -*-

from openerp import http
import json
from openerp.http import request, serialize_exception as _serialize_exception
from cStringIO import StringIO
from collections import deque
from datetime import datetime
from random import randint


class TGLController(http.Controller):
   
    @http.route('/test', auth='public')
    def handle_all(self, **kw):
        code = kw.get('id', False)
        if not code:
            return ''          

        dieuhoa_id = request.env['dieuhoa'].sudo().find_by_code(code)
        if not dieuhoa_id:
            return ''

        nhiet_do_phong = kw.get('temp', False) and float(kw.get('temp', False))
        
        if nhiet_do_phong < 10:
            return ''

        dieu_chinh = dieuhoa_id.calc_control(nhiet_do_phong)
        dieuhoa_id.write({
            'nhiet_do_phong': nhiet_do_phong,
        })
        print dieu_chinh
        if dieu_chinh == False:
            return ''

        control_state = 1 if dieuhoa_id.control_state else 0

        request.env['giatri'].sudo().create({
            'dieuhoa_id': dieuhoa_id.id,
            'nhiet_do_phong': nhiet_do_phong,
            'dong_dien': kw.get('curr', False) and float(kw.get('curr', False)),
            'dieu_chinh': dieu_chinh,
        })
        return 'qvl_m1={}&m2={}&state={}&end'.format(int(dieu_chinh), -5, control_state)