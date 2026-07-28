/*
Header file for offsetanchor

Holds a struct that corresponds to the python equivalent of the OffsetAnchor object
Doesn't have any of the same methods, only used for catching data from the NTPUpdater 
callback function.
*/

#pragma once // more modern way of doing ifndef
#include <cstdint> // necessary for int64_t

struct OffsetAnchor { // TODO: maybe just inherit this entire thing from python
    int64_t perf_ref{0}; // monotonic clock reference in nanoseconds TODO: this shouldnt be zero as default
    double time_ref{0.0};  // system clock reference in nanoseconds TODO: this shouldnt be zero as default
    double offset{0.0};    // offset in seconds
};