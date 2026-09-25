# NTPContinuousSync

Provides a clock that continuously syncs with NTP and learns to be more accurate over time.

## Quick Start Guide

To recieve the adjusted time, initialize an Endpoint and call the `easy_setup` method:
```
example_endpoint = Endpoint()
example_endpoint.easy_setup()
```
To the current adjusted time in seconds since epoch (January 1, 1970, 00:00:00 UTC), call the `now` method:
```
current_time = example_endpoint.now()
```

## Intended Use Case

## How It Works