from openmdao.api import ExplicitComponent
from input_params import max_n_turbines, n_quadrilaterals, separation_value_y
from transform_quadrilateral import AreaMapping
from numpy import sqrt


class MinDistance(ExplicitComponent):
    def setup(self):
        self.add_input("orig_layout", shape=(max_n_turbines, 2))
        self.add_input("turbine_radius", val=0.0)
        self.add_output("n_constraint_violations", val=0)


    def compute(self, inputs, outputs):
        layout = inputs["orig_layout"]
        radius = inputs["turbine_radius"]
        count = 0
        for t1 in range(len(layout)):
            for t2 in range(t1 + 1, len(layout)):
                count += self.distance(layout[t1], layout[t2]) <= 2.0 * radius
        outputs["n_constraint_violations"] = count


    def distance(self, t1, t2):
        return sqrt((t1[0] - t2[0]) ** 2.0 + (t1[1] - t2[1]) ** 2.0)


class WithinBoundaries(ExplicitComponent):
    def setup(self):
        self.add_input("layout", shape=(max_n_turbines, 2))
        self.add_input("area", shape=(n_quadrilaterals, 4, 2))

        self.add_output("n_constraint_violations", val=0)
        self.add_output("magnitude_violations", val=0.0)

    def compute(self, inputs, outputs):
        layout = inputs["layout"]
        squares = []
        for n in range(n_quadrilaterals):
            square = [[[n, 0.0], [n + 1, 0.0], [n + 1, 1.0], [n, 1.0]]]
            squares.append(square)
        area = inputs["area"]
        print square[0], area[0]
        maps = [AreaMapping(area[n], square[n]) for n in range(n_quadrilaterals)]
        count = 0
        magnitude = 0.0
        for t in layout:
            if t[1] < separation_value_y:
                mapped = maps[0].transform_to_rectangle(t[0], t[1])
            else:
                mapped = maps[1].transform_to_rectangle(t[0], t[1])
            c, m = self.inarea(mapped)
            count += c
            magnitude += m
        outputs["n_constraint_violations"] = count
        outputs["magnitude_violations"] = magnitude


    def inarea(self, mapped_turbine):
        count = 0
        magnitude = 0.0
        if mapped_turbine[0] < 0:
            magnitude += - mapped_turbine[0]
            count = 1
        elif mapped_turbine[0] > 1.0:
            magnitude += mapped_turbine[0] - 1.0
            count = 1
        if mapped_turbine[1] < 0:
            magnitude += - mapped_turbine[0]
            count = 1
        elif mapped_turbine[1] > 1.0:
            magnitude += mapped_turbine[1] - 1.0
            count = 1
        return count, magnitude