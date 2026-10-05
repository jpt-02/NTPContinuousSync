/*
Header file for sim_references
Lots of comments because I'm new to C++
*/

// Header Guards
#ifndef OFFSET_ANCHOR_HPP // ifndef = if not defined
#define OFFSET_ANCHOR_HPP

// Inform compiler that functions exists
struct OffsetAnchor { 
    double perf_ref; // monotonic clock reference (ns if opt1, ms if opt2)
    double time_ref;  // system clock reference (ns if opt1, ms if opt2)
    double offset;    // offset in seconds
};

OffsetAnchor create_offset_anchor(int optimization_flag, double offset);

#endif