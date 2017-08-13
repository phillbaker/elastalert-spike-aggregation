# elastalert-spike-aggregation

Elastalert includes (as of 8/2017) support for comparing the results of a period against the previous period ("[spike](http://elastalert.readthedocs.io/en/latest/ruletypes.html#spike)") and summing the values of a metric ("[metric aggregation](http://elastalert.readthedocs.io/en/latest/ruletypes.html#metric-aggregation)") but not doing both at the same time - handy for rules of the type "alert when the average value of inbound bytes per second has increased 3x over the previous hour."

## Usage

```yaml
name: "Disk IO Spike"

type: "elastalert_spike_aggregation.SpikeAggregationRule"

index: metricbeat-*

spike_height: 7
spike_type: up

# The size of the window used to determine average event frequency
# We use two sliding windows each of size timeframe
# To measure the 'reference' rate and the current rate
timeframe:
  hours: 30m

metric_agg_key: diskio.read.bytes
metric_agg_type: avg

query_key: beat.hostname

doc_type: metricsets

filter:
  - term:
      metricset.name: diskio

alert:
  - debug

```
