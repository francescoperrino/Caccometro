"""utils.normal_pdf replaces scipy.stats.norm.pdf (scipy is no longer a dependency)."""
import numpy as np
import pytest

import utils


@pytest.mark.parametrize("mean,std", [(0.0, 1.0), (0.37, 0.8), (2.5, 3.1), (10.0, 0.05)])
def test_matches_scipy_when_scipy_is_available(mean, std):
    stats = pytest.importorskip("scipy.stats")
    x = np.linspace(mean - 5 * std, mean + 5 * std, 101)
    assert np.allclose(utils.normal_pdf(x, mean, std), stats.norm.pdf(x, mean, std), rtol=1e-12, atol=0)
    assert np.isclose(utils.normal_pdf(mean, mean, std), stats.norm.pdf(mean, mean, std), rtol=1e-12)


def test_known_values_without_scipy():
    # standard normal: density at 0 is 1/sqrt(2*pi); at 1 it is exp(-1/2)/sqrt(2*pi)
    assert utils.normal_pdf(0, 0, 1) == pytest.approx(0.3989422804014327)
    assert utils.normal_pdf(1, 0, 1) == pytest.approx(0.24197072451914337)
    assert utils.normal_pdf(5, 3, 2) == pytest.approx(0.3989422804014327 / 2 * np.exp(-0.5))


def test_peak_is_at_the_mean_and_area_is_one():
    x = np.linspace(-30, 30, 60001)
    p = utils.normal_pdf(x, 1.5, 2.0)
    assert x[np.argmax(p)] == pytest.approx(1.5, abs=1e-3)
    area = float(np.sum((p[:-1] + p[1:]) / 2 * np.diff(x)))      # trapezoid rule
    assert area == pytest.approx(1.0, abs=1e-6)


def test_utils_does_not_import_scipy():
    import re
    source = open(utils.__file__, encoding="utf-8").read()
    assert not re.search(r"^\s*(import|from)\s+scipy", source, re.MULTILINE)
