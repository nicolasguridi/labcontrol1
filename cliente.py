from opcua import Client
import threading

class Cliente():
    def __init__(self, direccion, suscribir_eventos, SubHandler):
        self.direccion = direccion
        self.client = Client(direccion)
        self.alturas = {'H1': 0, 'H2': 0, 'H3':0, 'H4':0}
        self.temperaturas = {'T1': 0, 'T2': 0, 'T3':0, 'T4':0}
        self.valvulas = {'valvula1':0, 'valvula2':0}
        self.razones = {'razon1':0, 'razon2': 0}
        self.subscribir_eventos = suscribir_eventos
        self.periodo = 100 # cantidad de milisegundos para revisar las variables subscritas
        self.SubHandlerClass = SubHandler

    def instanciacion(self):
        self.root = self.client.get_root_node()
        self.objects = self.client.get_objects_node()
        self.Tanques = self.objects.get_child(['2:Proceso_Tanques','2:Tanques'])
        self.Valvulas = self.objects.get_child(['2:Proceso_Tanques', '2:Valvulas'])
        self.Razones = self.objects.get_child(['2:Proceso_Tanques', '2:Razones'])


        # Obtención de las alturas
        self.alturas['H1'] = self.Tanques.get_child(['2:Tanque1', '2:h'])
        self.alturas['H2'] = self.Tanques.get_child(['2:Tanque2', '2:h'])
        self.alturas['H3'] = self.Tanques.get_child(['2:Tanque3', '2:h'])
        self.alturas['H4'] = self.Tanques.get_child(['2:Tanque4', '2:h'])

        # Obtención de temperaturas
        self.temperaturas['T1'] = self.Tanques.get_child(['2:Tanque1', '2:T'])
        self.temperaturas['T2'] = self.Tanques.get_child(['2:Tanque2', '2:T'])
        self.temperaturas['T3'] = self.Tanques.get_child(['2:Tanque3', '2:T'])
        self.temperaturas['T4'] = self.Tanques.get_child(['2:Tanque4', '2:T'])

        # Obtención de los pumps
        self.valvulas['valvula1'] = self.Valvulas.get_child(['2:Valvula1', '2:u'])
        self.valvulas['valvula2'] = self.Valvulas.get_child(['2:Valvula2', '2:u'])

        # Obtención de los switches
        self.razones['razon1'] = self.Razones.get_child(['2:Razon1', '2:gamma'])
        self.razones['razon2'] = self.Razones.get_child(['2:Razon2', '2:gamma'])

        # Evento (alarma en este caso)
        if self.subscribir_eventos:
            self.myevent = self.root.get_child(["0:Types", "0:EventTypes", "0:BaseEventType", "2:Alarma_nivel"])#Tipo de evento
            self.obj_event = self.objects.get_child(['2:Proceso_Tanques', '2:Alarmas', '2:Alarma_nivel'])#Objeto Evento
            self.handler_event = self.SubHandlerClass()
            self.sub_event = self.client.create_subscription(self.periodo, self.handler_event)#Subscripción al evento
            self.handle_event = self.sub_event.subscribe_events(self.obj_event, self.myevent)


    def subscribir_cv(self): # Subscripción a las variables controladas
        self.handler_cv = self.SubHandlerClass()
        self.sub_cv = self.client.create_subscription(self.periodo, self.handler_cv)
        for key, var in self.alturas.items():
            self.sub_cv.subscribe_data_change(var)
        for key, var in self.temperaturas.items():
            self.sub_cv.subscribe_data_change(var)


    def subscribir_mv(self): # Subscripación a las variables manipuladas
        self.handler_mv = self.SubHandlerClass()
        self.sub_mv = self.client.create_subscription(self.periodo, self.handler_mv)
        for key, var in self.valvulas.items():
            self.sub_mv.subscribe_data_change(var)
        for key, var in self.razones.items():
            self.sub_mv.subscribe_data_change(var)


    def conectar(self):
        try:
            self.client.connect()
            self.objects = self.client.get_objects_node()
            print('Cliente OPCUA se ha conectado')
            self.instanciacion()

        except:
            self.client.disconnect()
            print('Cliente no se ha podido conectar')
