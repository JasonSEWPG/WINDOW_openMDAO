from openmdao.api import ExplicitComponent
from math import gamma
from numpy import exp
import numpy as np


class WindrosePreprocessor(ExplicitComponent):
    def __init__(self, n_real_directions, n_artificial_directions, n_windspeedbins):
        super(WindrosePreprocessor, self).__init__()
        self.n_directions = n_real_directions
        self.n_windspeedbins = n_windspeedbins

    def setup(self):
        self.add_input('cut_in', val=4.0)
        self.add_input('cut_out', val=25.0)
        self.add_input('weibull_shapes', shape=self.n_directions)
        self.add_input('weibull_scales', shape=self.n_directions)
        self.add_input('dir_probabilities', shape=self.n_directions)
        self.add_input('wind_directions', shape=self.n_directions)

        self.add_output('windrose_cases', shape=(self.n_artificial_directions * (self.n_windspeedbins + 1), 3))

    def compute(self, inputs, outputs):
        cut_in = inputs['cut_in']
        cut_out = inputs['cut_out']
        weibull_shapes = inputs['weibull_shapes']
        weibull_scales = inputs['weibull_scales']
        dir_probabilities = inputs['dir_probabilities']
        wind_directions = inputs['wind_directions']

        getdata = WeibullWindBins(weibull_shapes, weibull_scales, dir_probabilities, wind_directions, n_real_directions, n_artificial_directions, n_windspeedbins)
        getdata.cutin = cut_in
        getdata.cutout = cut_out

        wind_directions2, direction_probabilities2 = getdata.windrose.adapt_directions()
        wind_speeds2, wind_speeds_probabilities2 = getdata.speed_probabilities()

        outputs['windrose_cases'] = cases


class WeibullWindBins(object):

    def __init__(self, weibull_shapes, weibull_scales, dir_probabilities, direction, n_real_directions, n_artificial_directions, n_windspeedbins):
        self.weibull_scale = weibull_scales
        self.weibull_shape = weibull_shapes
        self.direction = direction
        self.dir_probability = dir_probabilities
        self.cutin = 0.0
        self.cutout = 0.0
        self.n_directions = n_real_directions
        self.n_windspeedbins = n_windspeedbins

        self.nbins = n_windspeedbins
        self.artificial_angle = n_artificial_directions
        self.real_angle = n_real_directions

    def adapt_directions(self):
        self.new_direction = []
        self.new_direction_probability = []
        self.new_weibull_scale = []
        self.new_weibull_shape = []
        self.new_direction2 = []
        self.new_direction_probability2 = []
        self.new_weibull_shape2 = []
        self.new_weibull_scale2 = []

        for i in range(len(self.direction)):
            if self.direction[i] % self.real_angle == 0.0:
                self.new_direction_probability.append(self.dir_probability[i])
                self.new_direction.append(self.direction[i])
                self.new_weibull_scale.append(self.weibull_scale[i])
                self.new_weibull_shape.append(self.weibull_shape[i])
            else:
                self.new_direction_probability[-1] += self.dir_probability[i]
        # print sum(self.dir_probability)
        # print self.new_direction
        # print self.new_direction_probability, sum(self.new_direction_probability)

        n = int(self.new_direction[1] - self.new_direction[0]) / int(self.artificial_angle)
        for i in range(len(self.new_direction)):
            for j in range(n):
                self.new_direction2.append(self.new_direction[i] + self.artificial_angle * j)
                self.new_direction_probability2.append(self.new_direction_probability[i] / n)
                self.new_weibull_scale2.append(self.new_weibull_scale[i])
                self.new_weibull_shape2.append(self.new_weibull_shape[i])

        return np.array(self.new_direction2), np.array(self.new_direction_probability2)

        # print self.new_direction2
        # print self.new_direction_probability2
        # print self.dir_probability

    def cumulative_weibull(self, wind_speed, weibull_scale_dir, weibull_shape_dir):

        return 1.0 - exp(-(wind_speed / weibull_scale_dir) ** weibull_shape_dir)

    def get_wind_speeds(self):
        delta = (self.cutout - self.cutin) / self.nbins
        windspeeds = []
        for i in range(self.nbins + 1):

            windspeeds.append(self.cutin + i * delta)

        return windspeeds

    def speed_probabilities(self):
        self.adapt_directions()
        speed_probabilities = []
        self.windspeeds = self.get_wind_speeds()

        for angle in self.new_direction2:
            place = self.new_direction2.index(angle)
            prob_cutout = (1.0 - self.cumulative_weibull(self.cutout, self.new_weibull_scale2[place], self.new_weibull_shape2[place]))
            length = len(self.windspeeds)
            windspeedprobabilities = [0.0 for _ in range(length)]

            for i in range(length):

                if i == 0:

                    windspeedprobabilities[i] = (self.cumulative_weibull(self.windspeeds[i], self.new_weibull_scale2[place], self.new_weibull_shape2[place]))

                elif i < length - 1:

                    windspeedprobabilities[i] = (self.cumulative_weibull(self.windspeeds[i], self.new_weibull_scale2[place], self.new_weibull_shape2[place]) - sum(windspeedprobabilities[:i]))

                elif i == length - 1:

                    windspeedprobabilities[i] = (self.cumulative_weibull(self.windspeeds[i], self.new_weibull_scale2[place], self.new_weibull_shape2[place]) - sum(windspeedprobabilities[:i]) + prob_cutout)

            speed_probabilities.append([item * 100.0 for item in windspeedprobabilities])

        return np.array(self.windspeeds), np.array(speed_probabilities)


if __name__ == '__main__':
    import itertools

    getdata = WeibullWindBins([0.01, 0.01], [10.0, 12.0], [25.0, 75.0], [0.0, 180.0], 180., 45., 1)
    getdata.cutin = 4.0
    getdata.cutout = 25.0

    wind_directions2, direction_probabilities2 = getdata.adapt_directions()
    wind_speeds2, wind_speeds_probabilities2 = getdata.speed_probabilities()

    cases = zip(wind_speeds2, wind_speeds_probabilities2)
    print cases

    cases_partial = list(itertools.product(wind_directions2, wind_speeds2.flatten()))
    print cases_partial


    print direction_probabilities2
    print wind_speeds_probabilities2
