from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.serializers import Serializer
from rest_framework import status
from curveengine import CurveEngine
import curveengine as ce
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import ORE
import requests
import json
from datetime import date
import Atlas

# Llamada para obtener curva dados ciertos parámetros.
def get_curves(paramsJson):
    # Cambiar esto por llamada a API Connect
    url='http://localhost:4000/api/v1/funding/curve/'+ json.dumps(paramsJson)
    data= requests.get(url)
    if data.status_code == 200:
        return data.json()
    else:
        return []

def generate_json(code, msg, data):
    response_data = {}
    response_data['code'] = code
    response_data['message'] = msg
    response_data['data'] = data
    return response_data

def date_parsed(dateParser):
    
    return 'valor'

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
            #version 1.1.2
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

        curvas = []
        for curve_name, curve in cm.curves.items():
            data_curve = []
            for item in curve.nodes():
                data_curve.append({
                                 'date': str(item[0].year())+'-'+str(item[0].month()).rjust(2, '0')+'-'+str(item[0].dayOfMonth()).rjust(2, '0'), 
                                 'value': item[1]
                                })
            curvas.append({ 'curveName': curve_name, 'nodes': data_curve })
            
        return Response(generate_json(200, 'OK', curvas))
    
class api_discount(APIView):
    # Start validation and return of curves from JSON required.
    @swagger_auto_schema(
        request_body=post_schema,
        responses=post_response,
        operation_description="Send JSON with data with the discount curves."
    )
    def post(self, request, format=None):
        serializer_class=Serializer
        #logging.warning(request.data)
        req = request.data
        #llamada 
        call_to_discount = get_curves(req)
        if (call_to_discount['code'] == 200):
            curve = call_to_discount['data'][0]
            dates = [ce.parseDate(node['date']) for node in curve['nodes']]
            values = [node['value'] for node in curve['nodes']]
            # se setea la fecha global para evitar errores de calculo
            ORE.Settings.instance().evaluationDate = dates[0]
            #Actual360 va fijo
            oreCurve = ORE.DiscountCurve(dates, values, ce.parseDayCounter('Actual360'))
            #se interpola y se estructura la respuesta
            responseDiscounts = []
            if ('dates' not in req):
                return Response(generate_json(200, 'You have not provided dates. The curve associated with the other delivered parameters is returned.', curve['nodes']))
            else:
                for requestedDate in req['dates']:
                    parsedDate = ce.parseDate(requestedDate) 
                    df = oreCurve.discount(parsedDate)
                    responseDiscounts.append({'date': requestedDate, 'value': df})
                #Valida que dates venga sino envía la curva
                if (len(req['dates'])==0):
                    return Response(generate_json(200, 'OK', curve['nodes']))
                else:
                    return Response(generate_json(200, 'OK', responseDiscounts))
        else:
            return Response(generate_json(call_to_discount['code'], call_to_discount['message'], ''))

class api_forward_rates(APIView):
    # Start validation and return of curves from JSON required.
    @swagger_auto_schema(
        request_body=post_schema,
        responses=post_response,
        operation_description="Send JSON with data with the forward rates."
    )
    def post(self, request, format=None):
        serializer_class=Serializer
        #logging.warning(request.data)
        req = request.data
        #llamada 
        call_to_discount = get_curves(req)
        if (call_to_discount['code'] == 200):
            curve = call_to_discount['data'][0]
            dates = [ce.parseDate(node['date']) for node in curve['nodes']]
            values = [node['value'] for node in curve['nodes']]
            # se setea la fecha global para evitar errores de calculo
            ORE.Settings.instance().evaluationDate = dates[0]
            #Actual360 va fijo
            oreCurve = ORE.DiscountCurve(dates, values, ce.parseDayCounter('Actual360'))
            #se interpola y se estructura la respuesta
            if ('dates' not in req):
                print(req)
                return Response(generate_json(200, 'You have not provided dates. The curve associated with the other delivered parameters is returned.', { "startDate": "", "endDate":"", "value":curve['nodes']}))
            else:
                for requestedDate in req['dates']:
                    startDate = ce.parseDate(requestedDate['startDate'])
                    endDate = ce.parseDate(requestedDate['endDate'])      
                    fwdRate = oreCurve.forwardRate(startDate, endDate, ce.parseDayCounter(req['dayCounter']), ce.parseCompounding(req['compounding'])).rate()
                    #Valida que dates venga sino envía la curva
                    if (len(req['dates'])==0):
                        return Response(generate_json(200, 'Sin ', curve['nodes']))
                    else:
                        return Response(generate_json(200, 'OK', { "startDate": requestedDate['startDate'], "endDate":requestedDate['endDate'], "value":fwdRate}))
        else:
            return Response(generate_json(call_to_discount['code'], call_to_discount['message'], ''))

class api_pricing_inicio_respaldo(APIView):
    # Start validation and return of curves from JSON required.
    @swagger_auto_schema(
        request_body=post_schema,
        responses=post_response,
        operation_description="Send JSON with data with the forward rates."
    )
    def post(self, request, format=None):
        serializer_class=Serializer
        #logging.warning(request.data)
        req = request.data
        try:
            tape = Atlas.Tape()
            print(type(tape))
        except:
            pass
        print(tape)
        
        evalDate = Atlas.Date(1, Atlas.August, 2020)
        store = Atlas.MarketStore(evalDate, Atlas.CLP()) # store with CLP as base currency

        # define curve
        curveDayCounter = Atlas.Actual360()
        curveCompounding = Atlas.Simple
        curveFrequency = Atlas.Annual
        clpRate = Atlas.Dual(0.03)
        usdRate = Atlas.Dual(0.01)
        fx = Atlas.Dual(800)
        tape.registerInput(clpRate) 
        tape.registerInput(usdRate) 
        tape.registerInput(fx) 
        tape.newRecording() # start recording, for later use
        
        strategy = Atlas.FlatForwardStrategy(evalDate, clpRate, curveDayCounter, curveCompounding, curveFrequency)
        clpCurve = Atlas.YieldTermStructure(strategy)
        index = Atlas.RateIndex(evalDate, curveFrequency, curveDayCounter, curveFrequency, curveCompounding)
        store.addCurve("CLP", clpCurve, index)
        
        # strategy = Atlas.FlatForwardStrategy(evalDate, usdRate, curveDayCounter, curveCompounding, curveFrequency)
        # usdCurve = Atlas.YieldTermStructure(strategy)
        # store.addCurve("USD", usdCurve, index)
        
        # add FX
        store.addExchangeRate(Atlas.CLP(), Atlas.USD(), fx)
        
        #define interest rate
        rateValue = Atlas.Dual(0.05)
        dayCounter = Atlas.Thirty360()
        compounding = Atlas.Simple
        frequency = Atlas.Annual
        
        rate = Atlas.InterestRate(rateValue, dayCounter, compounding, frequency)
        discountContext = store.curveContext("CLP")
        
        # define zero coupon instrument
        notional = 100
        startDate = evalDate
        endDate = Atlas.Date(1, Atlas.August, 2025)
        paymentFrequency = Atlas.Semiannual
        instrument = Atlas.FixedRateBulletInstrument(startDate, endDate, paymentFrequency, notional, rate, discountContext)
        
        indexer = Atlas.Indexer()
        indexer.visit(instrument)
        request = indexer.request()
        
        model = Atlas.SpotMarketDataModel(request, store)
        marketData = model.marketData(evalDate)
        
        npv = Atlas.Dual(0.0)
        tape.registerOutput(npv)

        npvCalculator = Atlas.NPVCalculator(marketData)
        npvCalculator.visit(instrument)
        npv = npvCalculator.results()
        print("NPV: {:.4f}".format(Atlas.getValue(npv)))

        return Response(generate_json(200, 'OK', "NPV: {:.4f}".format(Atlas.getValue(npv))))

class api_pricing(APIView):
    # Start validation and return of curves from JSON required.
    @swagger_auto_schema(
        request_body=post_schema,
        responses=post_response,
        operation_description="Send JSON with data with the forward rates."
    )
    def post(self, request, format=None):
        serializer_class=Serializer
        #logging.warning(request.data)
        req = request.data
        try:
            tape = Atlas.Tape()
        except Exception as e:
            pass
                
        #Tratamiento de fecha
        fechaDia = date.fromisoformat(req['refDate']).day
        fechaAno = date.fromisoformat(req['refDate']).year                
        if (date.fromisoformat(req['refDate']).month) == 1: 
            evalDate = Atlas.Date(fechaDia, Atlas.January, fechaAno) 
        elif (date.fromisoformat(req['refDate']).month) == 2:
            evalDate = Atlas.Date(fechaDia, Atlas.February, fechaAno)
        elif (date.fromisoformat(req['refDate']).month) == 3:
            evalDate = Atlas.Date(fechaDia, Atlas.March, fechaAno)
        elif (date.fromisoformat(req['refDate']).month) == 4:
            evalDate = Atlas.Date(fechaDia, Atlas.April, fechaAno)
        elif (date.fromisoformat(req['refDate']).month) == 5:
            evalDate = Atlas.Date(fechaDia, Atlas.May, fechaAno)
        elif (date.fromisoformat(req['refDate']).month) == 6:
            evalDate = Atlas.Date(fechaDia, Atlas.June, fechaAno)
        elif (date.fromisoformat(req['refDate']).month) == 7:
            evalDate = Atlas.Date(fechaDia, Atlas.July, fechaAno)
        elif (date.fromisoformat(req['refDate']).month) == 8:
            evalDate = Atlas.Date(fechaDia, Atlas.August, fechaAno)
        elif (date.fromisoformat(req['refDate']).month) == 9:
            evalDate = Atlas.Date(fechaDia, Atlas.September, fechaAno)
        elif (date.fromisoformat(req['refDate']).month) == 10:
            evalDate = Atlas.Date(fechaDia, Atlas.October, fechaAno)
        elif (date.fromisoformat(req['refDate']).month) == 11:
            evalDate = Atlas.Date(fechaDia, Atlas.November, fechaAno)            
        else:
            evalDate = Atlas.Date(fechaDia, Atlas.December, fechaAno)
       # Ejemplo
       # evalDate = Atlas.Date(1, Atlas.August, 2023)
        
        store = Atlas.MarketStore(evalDate, Atlas.CLP()) # store with CLP as base currency

        curves = {
            'curveName': 'CF_CLP',
            'nodes': {
                'node': '2023-06-28',
                'value': 1
            }
        }
        
        dates = [Atlas.parseISODate(node['date']) for node in curves['nodes']]
        values = [Atlas.Dual(node['value']) for node in curves['nodes']]
        
        #Calculo de CF no necesitamos setear monedas
        dayCounter = Atlas.Actual360()
        strategy = Atlas.DiscountLogLinearStrategy(dates, values, dayCounter)
        clpCurve = Atlas.YielTermStructure(strategy)
        store.addCurve(curves['curveName'], clpCurve)
        
        # define curve
        curveDayCounter = Atlas.Actual360()
        curveCompounding = Atlas.Simple
        curveFrequency = Atlas.Annual
        
        clpRate = Atlas.Dual(0.03)
        usdRate = Atlas.Dual(0.01)
        fx = Atlas.Dual(800)
        
        tape.registerInput(clpRate) 
        tape.registerInput(usdRate) 
        tape.registerInput(fx) 
        tape.newRecording() # start recording, for later use
        
        #Add CLP curve
        strategy = Atlas.FlatForwardStrategy(evalDate, clpRate, curveDayCounter, curveCompounding, curveFrequency)
        clpCurve = Atlas.YieldTermStructure(strategy)
        index = Atlas.RateIndex(evalDate, curveFrequency, curveDayCounter, curveFrequency, curveCompounding)
        store.addCurve("CLP", clpCurve, index)
        
        #Add USD curve
        strategy = Atlas.FlatForwardStrategy(evalDate, usdRate, curveDayCounter, curveCompounding, curveFrequency)
        usdCurve = Atlas.YieldTermStructure(strategy)
        store.addCurve("USD", usdCurve, index)
        
        # add FX
        store.addExchangeRate(Atlas.CLP(), Atlas.USD(), fx)
        
        #define interest rate
        rateValue = Atlas.Dual(0.05)
        dayCounter = Atlas.Thirty360()
        compounding = Atlas.Simple
        frequency = Atlas.Annual
        
        rate = Atlas.InterestRate(rateValue, dayCounter, compounding, frequency)
        discountContext = store.curveContext(curves['curveName'])
        
        # define zero coupon instrument
        notional = 100
        startDate = evalDate
        endDate = Atlas.Date(1, Atlas.August, 2025)
        paymentFrequency = Atlas.Semiannual
        
        ####Validar estos datos
        recalcNotionals='true'
        spread = 0.02 
        forecastCurveContext= ''
        
        #Seteo por instrumento que venga en el request
        if (req['structure'] == 'FixedRateBullet'):
            #instrument = Atlas.FixedRateBulletInstrument(startDate, endDate, paymentFrequency, notional, rate, discountContext)
            instrument = Atlas.FixedRateBulletInstrument(startDate, endDate, paymentFrequency, notional, rate, discountContext)
        elif (req['structure'] == 'FixedRateCustom'):
            instrument = Atlas.CustomFixedRateInstrument(dates, values, rate, discountContext)
        elif (req['structure'] == 'EqualPayments'):
            instrument = Atlas.EqualPaymentInstrument(startDate, endDate, paymentFrequency, notional, rate, discountContext, recalcNotionals)
        elif (req['structure'] == 'Zero'):
            instrument = Atlas.ZeroCouponInstrument(startDate, endDate, notional, rate, discountContext)
        elif (req['structure'] == 'FixedRateEqualRedemptions'):
            instrument = Atlas.FixedRateEqualRedemptionInstrument(startDate, endDate, paymentFrequency, notional, rate, discountContext)
        elif (req['structure'] == 'FloatingRateCustom'):
            instrument = Atlas.CustomFloatingRateInstrument(dates, values, spread, forecastCurveContext, discountContext)
        elif (req['structure'] == 'FloatingRateBullet'):
            instrument = Atlas.FloatingRateBulletInstrument(startDate, endDate, notional, spread, forecastCurveContext)
        else:
            #elif (req['structure'] == 'FloatingRateEqualRedemptions'):
            instrument = Atlas.FloatingRateEqualRedemptionInstrument(startDate, endDate, notional, spread, forecastCurveContext, discountContext)
            
        indexer = Atlas.Indexer()
        indexer.visit(instrument)
        request = indexer.request()
        
        model = Atlas.SpotMarketDataModel(request, store)
        marketData = model.marketData(evalDate)
        
        #Valorizacion
        npv = Atlas.Dual(0.0)
        tape.registerOutput(npv)

        npvCalculator = Atlas.NPVCalculator(marketData)
        npvCalculator.visit(instrument)
        npv = npvCalculator.results()
        print("NPV: {:.4f}".format(Atlas.getValue(npv)))
        
        #Tasa Par
        parSolver = Atlas.ParSolver(marketData)
        parSolver.visit(instrument)
        rate = parSolver.results()
        print("Par Rate: {:.4f}%".format(Atlas.getValue(rate)*100))

        # tabla de pagos
        profiler = Atlas.CashFlowProfiler()
        profiler.visit(instrument)
        interest = profiler.interests()
        redemptions = profiler.redemptions()

        return Response(generate_json(200, 'OK', {'nvp': Atlas.getValue(npv), 'cashflow': {'parRate': rate, 'interest': interest, 'redemptions': redemptions}}))