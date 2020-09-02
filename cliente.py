from opcua import Client
import threading

class Cliente():
    def __init__(self, direccion, SubHandler, suscribir_eventos=True):
        self.direccion = direccion
        self.client = Client(direccion)
        self.alturas = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}
        self.temperaturas = {'T1': 0, 'T2': 0, 'T3': 0, 'T4': 0}
        self.valvulas = {'valvula1': 0, 'valvula2': 0}
        self.razones = {'razon1': 0, 'razon2': 0}
        self.subscribir_eventos = suscribir_eventos
        self.periodo = 100
        self.SubHandlerClass = SubHandler

    def instanciacion(self):
        self.root = self.client.get_root_node()
        self.objects = self.client.get_objects_node()
        self.Tanques = self.objects.get_child(['2:Proceso_Tanques', '2:Tanques'])
        self.Valvulas = self.objects.get_child(['2:Proceso_Tanques', '2:Valvulas'])
        self.Razones = self.objects.get_child(['2:Proceso_Tanques', '2:Razones'])

        # for each tank
        for i in range(1, 5):
            # get height
            self.alturas[f'H{i}'] = self.Tanques.get_child([f'2:Tanque{i}', '2:h'])
            # get "temperature"
            self.temperaturas[f'T{i}'] = self.Tanques.get_child([f'2:Tanque{i}', '2:T'])

        # for each valve
        for i in [1, 2]:
            # get valve voltage
            self.valvulas[f'valvula{i}'] = self.Valvulas.get_child([f'2:Valvula{i}', '2:u'])
            # get gamma
            self.razones[f'razon{i}'] = self.Razones.get_child([f'2:Razon{i}', '2:gamma'])

        # event
        if self.subscribir_eventos:
            # event type
            self.myevent = self.root.get_child(["0:Types", "0:EventTypes", "0:BaseEventType", "2:Alarma_nivel"])
            # event object
            self.obj_event = self.objects.get_child(['2:Proceso_Tanques', '2:Alarmas', '2:Alarma_nivel'])
            self.handler_event = self.SubHandlerClass()
            # event subscription
            self.sub_event = self.client.create_subscription(self.periodo, self.handler_event)
            self.handle_event = self.sub_event.subscribe_events(self.obj_event, self.myevent)


    def conectar(self):
        try:
            self.client.connect()
            self.objects = self.client.get_objects_node()
            print('Cliente OPCUA se ha conectado')
            self.instanciacion()

        except:
            self.client.disconnect()
            print('Cliente no se ha podido conectar')
