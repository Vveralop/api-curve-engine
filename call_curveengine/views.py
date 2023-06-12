from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.serializers import Serializer
from rest_framework import status
from curveengine import CurveEngine
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

def generate_json(code, msg, data):
    response_data = {}
    response_data['code'] = code
    response_data['message'] = msg
    response_data['data'] = data
    return response_data

post_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'Json': openapi.Schema(type=openapi.TYPE_STRING, description='Request Curve Json'),
    },
    required=['Json']
)

post_response_ok= {
    status.HTTP_200_OK: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
           'Json': openapi.Schema(type=openapi.TYPE_OBJECT, description='Json')
        }
    ),
    status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
           'Json': openapi.Schema(type=openapi.TYPE_OBJECT, description='Other internal API issues')
        }
    ),
}

post_response = {
    status.HTTP_200_OK: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
           'Json': openapi.Schema(type=openapi.TYPE_OBJECT, description='Json with curves')
        }
    ),
    status.HTTP_406_NOT_ACCEPTABLE: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
           'Json': openapi.Schema(type=openapi.TYPE_OBJECT, description='Missing data')
        }
    ),
    status.HTTP_400_BAD_REQUEST: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
           'Json': openapi.Schema(type=openapi.TYPE_OBJECT, description='Bad json formatted')
        }
    ),
    status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
           'Json': openapi.Schema(type=openapi.TYPE_OBJECT, description='Other internal API issues')
        }
    ),
}

class api_health(APIView):
    @swagger_auto_schema(
        responses=post_response_ok,
        operation_description="Check if API service is up."
    )
    def get(self, request):
        status_date = datetime.today()
        status_api = {'API status': 'Api is running', 'time': status_date}
        return Response(status_api)

class api_bootstrap(APIView):
    # Start validation and return of curves from JSON required.
    @swagger_auto_schema(
        request_body=post_schema,
        responses=post_response,
        operation_description="Send JSON with data for the curves."
    )
    def post(self, request, format=None):
        serializer_class=Serializer
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
            data_curve = []
            for item in curve.nodes():
                data_curve.append({
                                 'date': str(item[0].year())+'-'+str(item[0].month()).rjust(2, '0')+'-'+str(item[0].dayOfMonth()).rjust(2, '0'), 
                                 'value': item[1]
                                })
            resp[curve_name] = data_curve
            
        return Response(generate_json(200, 'OK', resp))
