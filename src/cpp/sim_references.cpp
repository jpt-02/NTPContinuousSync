/*
Implementation file for sim_references
Lots of comments because I'm new to C++
*/

// imports
#include "sim_references.hpp"
#include <tuple> // imports tuple, which is the return value of sim reference functions
#include <cstdint> // gives us uint64_t, which is always 64 bits and can safely store large ms values
#include <chrono> // system clocks
#include "l1_clock.hpp" // custom ms-accurate clock thats faster than system calls

// Code

namespace chrono = std::chrono; // shortens import for usage in code

std::tuple<uint64_t, uint64_t, uint64_t> get_simultaneous_references() {
    /*
    Returns tup (p1, timeref, p2) of references. More precise, but slower.

    p references are only compatible with cpp steady clock (now python perftimer which has an indeterminate starting point)

    p1 and p2 are steady clock in ns. Technically 'since epoch', but since they aren't regularly synced its irrelevant.
    timeref is system clock since epoch in ns
    */
    // Get raw time references
    auto p1_raw = chrono::steady_clock::now(); // fastest way to get MONOTONIC time point without going bare metal
    auto timeref_raw = chrono::system_clock::now(); // fastest way to get SYSTEM time point without going bare metal
    auto p2_raw = chrono::steady_clock::now(); // same as p1_raw, just a little later
    
    // Convert raw references to numbers
    uint64_t p1 = chrono::duration_cast<chrono::nanoseconds>( 
        p1_raw.time_since_epoch()
    ).count();

    uint64_t timeref = chrono::duration_cast<chrono::nanoseconds>( 
        timeref_raw.time_since_epoch()
    ).count();

    uint64_t p2 = chrono::duration_cast<chrono::nanoseconds>( 
        p2_raw.time_since_epoch()
    ).count();

    // Make a tuple and return
    return std::make_tuple(p1, timeref, p2);
}


std::tuple<uint64_t, uint64_t, uint64_t> get_simultaneous_references_l1() {
    /*
    Returns tup (p1, timeref, p2) of references, using the custom l1 clock. Less precise, but faster.

    p references are only compatible with readings from l1 clock (not python perftimer or cpp steady clock)

    p1 and p2 are l1 (steady) clock in ms, since clock start.
    timeref is system clock since epoch in ns
    */
    // Get raw time references
    auto p1 = get_current_ms();
    auto timeref_raw = chrono::system_clock::now(); // fastest way to get SYSTEM time point without going bare metal
    auto p2 = get_current_ms();
    
    // Convert raw references to numbers
    uint64_t timeref = chrono::duration_cast<chrono::milliseconds>(
        timeref_raw.time_since_epoch()
    ).count();

    // Make a tuple and return
    return std::make_tuple(p1, timeref, p2);
}