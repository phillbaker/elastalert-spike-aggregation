def test_rule():
    rules = {'buffer_time': datetime.timedelta(minutes=5),
             'timestamp_field': '@timestamp',
             'metric_agg_type': 'avg',
             'metric_agg_key': 'cpu_pct'}

    # Check threshold logic
    with pytest.raises(EAException):
        rule = MetricAggregationRule(rules)

    rules['min_threshold'] = 0.1
    rules['max_threshold'] = 0.8

    rule = MetricAggregationRule(rules)

    assert rule.rules['aggregation_query_element'] == {'cpu_pct_avg': {'avg': {'field': 'cpu_pct'}}}

    assert rule.crossed_thresholds(None) is False
    assert rule.crossed_thresholds(0.09) is True
    assert rule.crossed_thresholds(0.10) is False
    assert rule.crossed_thresholds(0.79) is False
    assert rule.crossed_thresholds(0.81) is True

    rule.check_matches(datetime.datetime.now(), None, {'cpu_pct_avg': {'value': None}})
    rule.check_matches(datetime.datetime.now(), None, {'cpu_pct_avg': {'value': 0.5}})
    assert len(rule.matches) == 0

    rule.check_matches(datetime.datetime.now(), None, {'cpu_pct_avg': {'value': 0.05}})
    rule.check_matches(datetime.datetime.now(), None, {'cpu_pct_avg': {'value': 0.95}})
    assert len(rule.matches) == 2

    rules['query_key'] = 'qk'
    rule = MetricAggregationRule(rules)
    rule.check_matches(datetime.datetime.now(), 'qk_val', {'cpu_pct_avg': {'value': 0.95}})
    assert rule.matches[0]['qk'] == 'qk_val'



    # Events are 1 per second
    events = hits(100, timestamp_field='ts')

    # Constant rate, doesn't match
    rules = {'threshold_ref': 10,
             'spike_height': 2,
             'timeframe': datetime.timedelta(seconds=10),
             'spike_type': 'both',
             'use_count_query': False,
             'timestamp_field': 'ts'}
    rule = SpikeRule(rules)
    rule.add_data(events)
    assert len(rule.matches) == 0

    # Double the rate of events after [50:]
    events2 = events[:50]
    for event in events[50:]:
        events2.append(event)
        events2.append({'ts': event['ts'] + datetime.timedelta(milliseconds=1)})
    rules['spike_type'] = 'up'
    rule = SpikeRule(rules)
    rule.add_data(events2)
    assert len(rule.matches) == 1

    # Doesn't match
    rules['spike_height'] = 3
    rule = SpikeRule(rules)
    rule.add_data(events2)
    assert len(rule.matches) == 0

    # Downward spike
    events = events[:50] + events[75:]
    rules['spike_type'] = 'down'
    rule = SpikeRule(rules)
    rule.add_data(events)
    assert len(rule.matches) == 1

    # Doesn't meet threshold_ref
    # When ref hits 11, cur is only 20
    rules['spike_height'] = 2
    rules['threshold_ref'] = 11
    rules['spike_type'] = 'up'
    rule = SpikeRule(rules)
    rule.add_data(events2)
    assert len(rule.matches) == 0

    # Doesn't meet threshold_cur
    # Maximum rate of events is 20 per 10 seconds
    rules['threshold_ref'] = 10
    rules['threshold_cur'] = 30
    rule = SpikeRule(rules)
    rule.add_data(events2)
    assert len(rule.matches) == 0

    # Alert on new data
    # (At least 25 events occur before 30 seconds has elapsed)
    rules.pop('threshold_ref')
    rules['timeframe'] = datetime.timedelta(seconds=30)
    rules['threshold_cur'] = 25
    rules['spike_height'] = 2
    rules['alert_on_new_data'] = True
    rule = SpikeRule(rules)
    rule.add_data(events2)
    assert len(rule.matches) == 1
