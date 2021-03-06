from openmdao.api import ExplicitComponent


class AEP(ExplicitComponent):

    def setup(self):
        self.add_input('aeroAEP', val=0.0)
        self.add_input('availability', val=0.0)
        self.add_input('electrical_efficiency', val=0.0)

        self.add_output('AEP', val=0.0)

    def compute(self, inputs, outputs):
        outputs['AEP'] = inputs['aeroAEP'] * inputs['availability'] * inputs['electrical_efficiency']
