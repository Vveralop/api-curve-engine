from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.decorators import api_view
from curveengine import CurveEngine
import logging

def generate_json(code, msg, data):
    response_data = {}
    response_data['code'] = code
    response_data['message'] = msg
    response_data['data'] = data
    return response_data

class API(GenericAPIView):

    def getData(self, request):
        person = {'name': 'Dennis', 'age': 28}
        return Response(person)

    # Start validation and return of curves from JSON required.
    def bootstrap(self, request):
        #logging.warning(request.data)
        try:
            #version 1.1.0
            #cm = CurveEngine(request.data)
            #version 1.1.1
            cm = CurveEngine(data=request.data, curves={}, indexes={})
        except Exception as e:
            if (str(e)=='Invalid configuration'):
                code = 406
                error = str(e.__cause__)
                if (error=='None'):
                    error = str(e)
                else:
                    if (str(e.__cause__.__cause__)=='None'):
                        error = str(e.__cause__)
                    else:
                        if (str(e.__cause__.__cause__.__cause__)=='None'):
                            error = str(e.__cause__.__cause__)
                        else:
                            if (str(e.__cause__.__cause__.__cause__.__cause__) == 'None'):
                                error = str(e.__cause__.__cause__.__cause__)
                            else:
                                if (str(e.__cause__.__cause__.__cause__.__cause__.__cause__) == 'None'):
                                    error = str(e.__cause__.__cause__.__cause__.__cause__)
                                else:
                                    if (str(e.__cause__.__cause__.__cause__.__cause__.__cause__.__cause__) == 'None'):
                                        error = str(e.__cause__.__cause__.__cause__.__cause__.__cause__)
            else:
                code = e.status_code
                error = str(e)
            return Response(generate_json(code, error, ''), status=code)

        resp = {}
        for curve_name, curve in cm.curves.items():
            nodes = {}
            for item in curve.nodes():
                date = str(item[0].year())+'-'+str(item[0].month()).rjust(2, '0')+'-'+str(item[0].dayOfMonth()).rjust(2, '0')
                value = item[1]
                nodes[date] = value
                

            resp[curve_name] = nodes
        return Response(generate_json(200, 'OK', resp))
