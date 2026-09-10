import numpy as np
import pytest

from caste_in_common.stats import binned_overlap, cdf, pairwise, quantile


def test_threshold_ties_and_zeros():
    x, w = [0, 1, 1, 3], [1, 2, 3, 4]
    np.testing.assert_allclose(cdf(x, w, [0, 1, 3]), [0.1, 0.6, 1])
    np.testing.assert_allclose(cdf(x, w, [0, 1, 3], inclusive=False), [0, 0.1, 0.6])
    np.testing.assert_allclose(cdf(x, w, [-np.inf, np.inf]), [0, 1])


def test_pairwise_against_enumeration():
    a, wa, b, wb = [0, 1, 3], [2, 1, 3], [0, 1, 2], [1, 3, 2]
    expected = np.zeros(3)
    for x, wx in zip(a, wa):
        for y, wy in zip(b, wb):
            expected[0 if x < y else 1 if x == y else 2] += wx * wy
    expected /= sum(wa) * sum(wb)
    actual = pairwise(a, wa, b, wb)
    np.testing.assert_allclose(actual[:3], expected)
    assert sum(actual[:3]) == pytest.approx(1)
    assert actual[3] == pytest.approx(expected[0] + expected[1] / 2)
    assert actual[3] + pairwise(b, wb, a, wa)[3] == pytest.approx(1)


def test_pairwise_identical_and_separated():
    assert pairwise([0], [1], [0], [1]) == (0, 1, 0, 0.5)
    assert pairwise([0], [1], [1], [1]) == (1, 0, 0, 1)


def test_quantile_and_rescaling():
    assert quantile([0, 1, 2], [1, 1, 2], 0.5) == 1
    assert quantile([0, 1, 2], [1, 1, 2], 1) == 2
    np.testing.assert_allclose(
        cdf([0, 1], [1, 2], [0, 1]), cdf([0, 1], [10, 20], [0, 1])
    )


def test_overlap_depends_on_bins():
    assert binned_overlap([0], [1], [1], [1], [-np.inf, 0.5, np.inf]) == 0
    assert binned_overlap([0], [1], [1], [1], [-np.inf, np.inf]) == 1


@pytest.mark.parametrize(
    "x,w",
    [
        ([], []),
        ([1], [0]),
        ([1], [-1]),
        ([np.nan], [1]),
        ([1], [np.inf]),
        ([1, 2], [1]),
    ],
)
def test_invalid_distributions_fail(x, w):
    with pytest.raises(ValueError):
        cdf(x, w, [1])
