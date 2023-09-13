"""Test for updater.particle module"""
import datetime
from functools import partial

import numpy as np
import pytest

from ...models.measurement.linear import LinearGaussian
from ...resampler.particle import SystematicResampler
from ...types.array import StateVectors
from ...types.detection import Detection
from ...types.hypothesis import SingleHypothesis
from ...types.particle import Particle
from ...types.prediction import (
    ParticleStatePrediction, ParticleMeasurementPrediction)
from ...updater.particle import (
    ParticleUpdater, GromovFlowParticleUpdater,
    GromovFlowKalmanParticleUpdater)


def dummy_constraint_function(particles):
    part_indx = particles.state_vector[1, :] > 20
    return part_indx


@pytest.fixture(params=(
        ParticleUpdater,
        partial(ParticleUpdater, resampler=SystematicResampler()),
        GromovFlowParticleUpdater,
        GromovFlowKalmanParticleUpdater,
        partial(ParticleUpdater, constraint_func=dummy_constraint_function)))
def updater(request):
    updater_class = request.param
    measurement_model = LinearGaussian(
        ndim_state=2, mapping=[0], noise_covar=np.array([[0.04]]))
    return updater_class(measurement_model)


def test_particle(updater):
    # Measurement model
    timestamp = datetime.datetime.now()
    particles = [Particle([[10], [10]], 1 / 9),
                 Particle([[10], [20]], 1 / 9),
                 Particle([[10], [30]], 1 / 9),
                 Particle([[20], [10]], 1 / 9),
                 Particle([[20], [20]], 1 / 9),
                 Particle([[20], [30]], 1 / 9),
                 Particle([[30], [10]], 1 / 9),
                 Particle([[30], [20]], 1 / 9),
                 Particle([[30], [30]], 1 / 9),
                 ]

    prediction = ParticleStatePrediction(None, particle_list=particles,
                                         timestamp=timestamp)
    measurement = Detection([[20.0]], timestamp=timestamp)
    eval_measurement_prediction = ParticleMeasurementPrediction(None, particle_list=[
                                            Particle(i.state_vector[0, :], 1 / 9)
                                            for i in particles],
                                            timestamp=timestamp)

    measurement_prediction = updater.predict_measurement(prediction)

    assert np.all(eval_measurement_prediction.state_vector == measurement_prediction.state_vector)
    assert measurement_prediction.timestamp == timestamp

    updated_state = updater.update(SingleHypothesis(
        prediction, measurement, measurement_prediction))

    # Don't know what the particles will exactly be due to randomness so check
    # some obvious properties

    if hasattr(updater, 'constraint_func') and updater.constraint_func is not None:
        indx = dummy_constraint_function(prediction)
        assert np.all(updated_state.weight[indx] == 0)

    assert np.isclose(np.sum(updated_state.weight.astype(np.float_)), 1.0, rtol=1e-5)
    assert updated_state.timestamp == timestamp
    assert updated_state.hypothesis.measurement_prediction == measurement_prediction
    assert updated_state.hypothesis.prediction == prediction
    assert updated_state.hypothesis.measurement == measurement
    if hasattr(updater, 'constraint_func') and updater.constraint_func is not None:
        assert np.allclose(updated_state.mean, StateVectors([[20.0], [15.0]]), rtol=2e-2)
    else:
        assert np.allclose(updated_state.mean, StateVectors([[20.0], [20.0]]), rtol=2e-2)
