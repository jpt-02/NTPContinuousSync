# NTPContinuousSync

Provides a clock that continuously syncs with NTP and learns to be more accurate over time.

## Quick Start Guide

First, initialize an instance of the QuickStart class:
```
example_endpoint = QuickStart()
```
To the current adjusted time in seconds since epoch (January 1, 1970, 00:00:00 UTC), call the `now` method:
```
current_time = example_endpoint.now()
```

## Intended Use Case

## How It Works