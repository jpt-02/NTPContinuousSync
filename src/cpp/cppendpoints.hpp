/*
Header file for cppendpoints
*/

#pragma once // modern version of indef

#include "offsetanchor.hpp" // includes offset anchor for time references
#include <mutex> // mutual exclusion lock, prevents race conditions

class cppSimpleEndpoint { // TODO: annotate all of this
private:
    mutable std::mutex lock_;
    OffsetAnchor offset_anchor_; // Initialize an empty offset anchor

public:
    cppSimpleEndpoint();
    void update_anchor(int64_t perf_ref, double time_ref, double offset);
    double now() const;
};