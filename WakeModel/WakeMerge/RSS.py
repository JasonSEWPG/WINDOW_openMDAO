from openmdao.api import ExplicitComponent, Group
from input_params import max_n_turbines
from numpy import sqrt
import numpy as np
from src.api import AbstractWakeMerge


class MergeRSS(AbstractWakeMerge):

    def merge_model(self, defs):  

        sq = defs ** 2.0
        summation = sum(sq)
        case_ans = sqrt(summation)
        return case_ans


if __name__ == '__main__':
    from openmdao.api import Problem, Group, IndepVarComp
    from numpy import sqrt

    model = Group()
    ivc = IndepVarComp()

    ivc.add_output('deficits', [0.16, 0.14, 0.15, 0.18])

    model.add_subsystem('indep', ivc)
    model.add_subsystem('rms', WakeMergeRSS(4))

    model.connect('indep.deficits', 'rms.all_du')

    prob = Problem(model)
    prob.setup()
    prob.run_model()
    print(prob['rms.u'])
