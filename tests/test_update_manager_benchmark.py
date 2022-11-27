import pytest

from smartbox.update_manager import DevDataSubscription, UpdateSubscription


@pytest.mark.benchmark
def test_benchmark_dev_data_subscription_create(benchmark):
    def callback(data):
        pass

    benchmark(DevDataSubscription, ".away_status", callback)


@pytest.mark.benchmark
def test_benchmark_dev_data_subscription_eval(benchmark):
    def callback(data):
        pass

    sub = DevDataSubscription(".away_status", callback)
    data = {"away_status": {"away": False}}

    benchmark(sub.match, data)


@pytest.mark.benchmark
def test_benchmark_update_subscription_create(benchmark):
    def callback(data):
        pass

    benchmark(UpdateSubscription, "/foo", ".body", callback)


@pytest.mark.benchmark
def test_benchmark_update_subscription_eval(benchmark):
    def callback(data):
        pass

    sub = UpdateSubscription("/foo", ".body.power_limit", callback)
    data = {"path": "/foo", "body": {"away_status": {"away": False}}}

    benchmark(sub.match, data)
