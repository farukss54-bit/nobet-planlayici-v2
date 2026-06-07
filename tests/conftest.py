"""
Pytest fixture'ları.
"""

import pytest
from scenarios import ScenarioGenerator
from tests._helpers import scenario_to_solver_input


@pytest.fixture
def easy_input():
    gen = ScenarioGenerator(seed=42)
    data = gen.generate(difficulty="easy", yil=2025, ay=2, num_personel=10)
    return scenario_to_solver_input(data)


@pytest.fixture
def normal_input():
    gen = ScenarioGenerator(seed=123)
    data = gen.generate(difficulty="normal", yil=2025, ay=3, num_personel=15)
    return scenario_to_solver_input(data)


@pytest.fixture
def nightmare_input():
    gen = ScenarioGenerator(seed=999)
    data = gen.generate(difficulty="nightmare", yil=2025, ay=4, num_personel=8)
    return scenario_to_solver_input(data)
