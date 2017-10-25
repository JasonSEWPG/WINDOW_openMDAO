from src.api import WakeModel
from WakeModel.jensen import JensenWakeFraction, JensenWakeDeficit
from openmdao.api import IndepVarComp, Problem, Group, view_model, ParallelGroup
import numpy as np
from time import time
from Power.power_models import PowerPolynomial
from input_params import turbine_radius
from WakeModel.WakeMerge.RSS import WakeMergeRSS
from src.api import AEPWorkflow

real_angle = 180.0
artificial_angle = 60.0
n_windspeedbins = 2


class WorkingGroup(Group):
    def __init__(self, power_model, fraction_model, deficit_model, merge_model):
        super(WorkingGroup, self).__init__()
        self.power_model = power_model
        self.fraction_model = fraction_model
        self.deficit_model = deficit_model
        self.merge_model = merge_model

    def setup(self):
        indep2 = self.add_subsystem('indep2', IndepVarComp())
        # indep2.add_output('layout', val=read_layout('horns_rev9.dat'))
        indep2.add_output('layout', val=np.array([[0, 0.0, 0.0], [1, 560.0, 0.0], [2, 1120.0, 0.0], [3, 1680.0, 0.0],
                                                  [4, 0.0, 1120.0], [5, 0.0, 1120.0], [6, 0.0, 1120.0],
                                                  [7, 0.0, 1120.0], [8, 0.0, 1120.0], [9, 0.0, 1120.0]]))
        # indep2.add_output('layout', val=np.array(
        #     [[0, 0.0, 0.0], [1, 560.0, 560.0], [2, 1120.0, 1120.0], [3, 1120.0, 0.0], [4, 0.0, 1120.0],
        #     [5, 6666.6, 6666.6], [6, 6666.6, 6666.6], [7, 6666.6, 6666.6], [8, 6666.6, 6666.6], [9, 6666.6, 6666.6]]))
        # indep2.add_output('layout', val=np.array([[0, 0.0, 0.0], [1, 560.0, 560.0], [2, 1120.0, 1120.0],
        # [3, 1120.0, 0.0], [4, 0.0, 1120.0], [5, float('nan'), float('nan')]]))
        indep2.add_output('weibull_shapes', val=[0.01, 0.01])
        indep2.add_output('weibull_scales', val=[10.0, 12.0])
        indep2.add_output('dir_probabilities', val=[25.0, 75.0])
        indep2.add_output('wind_directions', val=[0.0, 180.0])
        indep2.add_output('cut_in', val=4.0)
        indep2.add_output('cut_out', val=25.0)
        indep2.add_output('r', val=40.0)
        indep2.add_output('n_turbines', val=4)
        indep2.add_output('freestream', val=[8.5, 8.0])
        indep2.add_output('angle', val=[90.0, 270.0])  # Follows windrose convention N = 0 deg, E = 90 deg, S = 180 deg,
        # W = 270 deg
        self.add_subsystem('AEP', AEPWorkflow(real_angle, artificial_angle, n_windspeedbins))

        self.connect('indep2.layout', 'AEP.original')
        self.connect('indep2.n_turbines', 'AEP.n_turbines')
        self.connect('indep2.r', 'AEP.r')
        self.connect('indep2.cut_in', 'AEP.cut_in')
        self.connect('indep2.cut_out', 'AEP.cut_out')
        self.connect('indep2.weibull_shapes', 'AEP.weibull_shapes')
        self.connect('indep2.weibull_scales', 'AEP.weibull_scales')
        self.connect('indep2.dir_probabilities', 'AEP.dir_probabilities')
        self.connect('indep2.wind_directions', 'AEP.wind_directions')


def read_layout(layout_file):
    layout_file = open(layout_file, 'r')
    layout = []
    i = 0
    for line in layout_file:
        columns = line.split()
        layout.append([i, float(columns[0]), float(columns[1])])
        i += 1

    return np.array(layout)


prob = Problem()
prob.model = WorkingGroup(PowerPolynomial, JensenWakeFraction, JensenWakeDeficit, WakeMergeRSS)
prob.setup()
start = time()
prob.run_model()
print time() - start, "seconds"
for nn in range(4):
    print [ind for ind in prob['parallel.wake{}.wakemodel.U'.format(nn)] if ind > 0]
    print prob['parallel.wake{}.farmpower.farm_power'.format(nn)]

# view_model(prob)
# data = prob.check_totals(of=['farmpower.farm_power'], wrt=['indep2.k'])
# print data
# data = prob.check_partials(suppress_output=True)
# print(data['farmpower']['farm_power', 'ind_powers'])
# prob.model.list_outputs()
