/*
Implementation file for sim_references

The purpose of this file is to ensure that time references (one for monotonic clock and one for system clock) are 
acquired as close to one another as possible. To make this happen, one system time reference is taken between two 
monotonic references, and this is looped 10 times to get the smallest possible window where all 3 are acquired. The 
two monotonic references are then averaged, meaning our maximum possible error as a result of reference acquisitions 
is the size of the window. References using chrono are taken in raw form before being parsed to make the loop as quick 
as possible.
*/

// imports
#include "offset_anchor.hpp"
#include <cstdint> // gives us uint64_t, which is always 64 bits and can safely store large ms values
#include <chrono> // system clocks
#include "l1_clock.hpp" // custom ms-accurate clock thats faster than system calls
#include <vector>
#include <string>
#include <stdexcept>

// Code

namespace chrono = std::chrono; // shortens import for usage in code

// STRUCTS

struct RawReferences_opt1 {
    chrono::steady_clock::time_point p1_raw;
    chrono::system_clock::time_point timeref_raw;
    chrono::steady_clock::time_point p2_raw;
};

struct RawReferences_opt2 {
    uint64_t p1_raw;
    chrono::system_clock::time_point timeref_raw;
    uint64_t p2_raw;
};

struct ParsedReferences {
    uint64_t p1;
    uint64_t timeref;
    uint64_t p2;
};

struct ConstrainedReferences {
    uint64_t time_ref;
    uint64_t perf_ref;
};

// FUNCTIONS

RawReferences_opt1 get_raw_references_opt1() {
    /*
    Gets raw clock references for opt1.

    Returns: {monotonic clock time point, system clock time point, monotonic clock time point}
    */
    auto p1_raw = chrono::steady_clock::now();
    auto timeref_raw = chrono::system_clock::now();
    auto p2_raw = chrono::steady_clock::now();
    return {p1_raw, timeref_raw, p2_raw};
}

RawReferences_opt2 get_raw_references_opt2() {
    /*
    Gets raw clock references for opt2.

    Returns: {int: l1_clock time in ms, system clock time point, int: l1_clock time in ms}
    */
    auto p1 = get_current_ms();
    auto timeref_raw = chrono::system_clock::now();
    auto p2 = get_current_ms();
    return {p1, timeref_raw, p2};
}

ParsedReferences process_references_opt1(const RawReferences_opt1& raw) { // & means pass as reference instead of copying
    /*
    Gets parsed references for opt1.

    Returns: {int: monotonic time in ns, int: system time in ns, int: monotonic time in ns}
    */
    const auto & [p1_raw, timeref_raw, p2_raw] = raw;

    uint64_t p1 = chrono::duration_cast<chrono::nanoseconds>( 
        p1_raw.time_since_epoch()
    ).count();

    uint64_t timeref = chrono::duration_cast<chrono::nanoseconds>( 
        timeref_raw.time_since_epoch()
    ).count();

    uint64_t p2 = chrono::duration_cast<chrono::nanoseconds>( 
        p2_raw.time_since_epoch()
    ).count();

    return {p1, timeref, p2};
}

ParsedReferences process_references_opt2(const RawReferences_opt2& raw) {
    /*
    Gets raw clock references for opt2.

    Returns: {int: l1_clock time in ms, int: system time in ms, int: l1_clock time in ms}
    */
    const auto & [p1, timeref_raw, p2] = raw;

    uint64_t timeref = chrono::duration_cast<chrono::milliseconds>(
        timeref_raw.time_since_epoch()
    ).count();

    // Make a tuple and return
    return {p1, timeref, p2};
}

ConstrainedReferences get_constrained_references_opt1() {
    /*
    Loops through 10 pairs of raw references, parses them, and returns the pair of parsed 
    references with the smallest time window between p1 and p2. 

    Returns: {int: system time in ns, int: monotonic time in ns}
    */
    
    // quickly get all raw references
    std::vector<RawReferences_opt1> history;
    history.reserve(10); // Reserves memory so the loop stays fast
    for (int i=0; i<10; i++) {
        RawReferences_opt1 result = get_raw_references_opt1();

        history.push_back(result);
    }

    // parse references and do math
    uint64_t min_distance = UINT64_MAX;
    ParsedReferences best_parsed{};
    for (int i = 0; i < 10; i++) {
        ParsedReferences parsed = process_references_opt1(history[i]);
        
        // Calculate absolute distance between p1 and p2
        uint64_t dist = (parsed.p1 > parsed.p2) ? (parsed.p1 - parsed.p2) : (parsed.p2 - parsed.p1);

        if (dist < min_distance) {
            min_distance = dist;
            best_parsed = parsed;
        }
    }

    // Return the timeref and the average of p1 and p2
    ConstrainedReferences constrained_ref;
    constrained_ref.time_ref = best_parsed.timeref;
    constrained_ref.perf_ref = (best_parsed.p1 + best_parsed.p2) / 2;

    return constrained_ref;
}

ConstrainedReferences get_constrained_references_opt2() {
    /*
    Loops through 10 pairs of raw references, parses them, and returns the pair of parsed 
    references with the smallest time window between p1 and p2. 

    Returns: {int: system time in ms, int: l1_clock time in ms}
    */
    
    // quickly get all raw references
    std::vector<RawReferences_opt2> history;
    history.reserve(10); // Reserves memory so the loop stays fast
    for (int i=0; i<10; i++) {
        RawReferences_opt2 result = get_raw_references_opt2();

        history.push_back(result);
    }

    // parse references and do math
    uint64_t min_distance = UINT64_MAX;
    ParsedReferences best_parsed{};
    for (int i = 0; i < 10; i++) {
        ParsedReferences parsed = process_references_opt2(history[i]);
        
        // Calculate absolute distance between p1 and p2
        uint64_t dist = (parsed.p1 > parsed.p2) ? (parsed.p1 - parsed.p2) : (parsed.p2 - parsed.p1);

        if (dist < min_distance) {
            min_distance = dist; // TODO: put some prints in here to see if its working correctly
            best_parsed = parsed;
        }
    }

    // Return the timeref and the average of p1 and p2
    ConstrainedReferences constrained_ref;
    constrained_ref.time_ref = best_parsed.timeref;
    constrained_ref.perf_ref = (best_parsed.p1 + best_parsed.p2) / 2;

    return constrained_ref;
}

OffsetAnchor create_offset_anchor(int optimization_flag, double offset) {
    /*
    Creates an offset anchor with an offset, time_ref, and perf_ref

    If optimization flag is 2, l1_clock must be started before initializing this

    Returns: {double: offset anchor in s, double: time_ref, double: perf_ref}
            units for time_ref and perf_ref: ns if opt1, ms if opt2
    */
    OffsetAnchor return_anchor{};
    return_anchor.offset = offset; // in future, maybe round this for opt2 to save memory?
    if (optimization_flag == 1) {
        ConstrainedReferences references = get_constrained_references_opt1();
        return_anchor.time_ref = references.time_ref;
        return_anchor.perf_ref = references.perf_ref;
    } else if (optimization_flag == 2) {
        ConstrainedReferences references = get_constrained_references_opt2();
        return_anchor.time_ref = references.time_ref;
        return_anchor.perf_ref = references.perf_ref;
    } else {
        throw std::invalid_argument("Unsupported optimization_flag: " + std::to_string(optimization_flag));
    }
    return return_anchor;
}


// OLD FUNCS ---------------------------------------

// std::tuple<uint64_t, uint64_t, uint64_t> get_simultaneous_references() {
//     /*
//     Returns tup (p1, timeref, p2) of references. More precise, but slower.

//     p references are only compatible with cpp steady clock (now python perftimer which has an indeterminate starting point)

//     p1 and p2 are steady clock in ns. Technically 'since epoch', but since they aren't regularly synced its irrelevant.
//     timeref is system clock since epoch in ns
//     */
//     // Get raw time references
//     auto p1_raw = chrono::steady_clock::now(); // fastest way to get MONOTONIC time point without going bare metal
//     auto timeref_raw = chrono::system_clock::now(); // fastest way to get SYSTEM time point without going bare metal
//     auto p2_raw = chrono::steady_clock::now(); // same as p1_raw, just a little later
//     // TODO: take everything below out of this function and make another to do this 10 times or whatever and do all the math afterwards. just keep it in this file for simplicity's sake.
//     // Convert raw references to numbers
//     uint64_t p1 = chrono::duration_cast<chrono::nanoseconds>( 
//         p1_raw.time_since_epoch()
//     ).count();

//     uint64_t timeref = chrono::duration_cast<chrono::nanoseconds>( 
//         timeref_raw.time_since_epoch()
//     ).count();

//     uint64_t p2 = chrono::duration_cast<chrono::nanoseconds>( 
//         p2_raw.time_since_epoch()
//     ).count();

//     // Make a tuple and return
//     return std::make_tuple(p1, timeref, p2);
// }


// std::tuple<uint64_t, uint64_t, uint64_t> get_simultaneous_references_l1() {
//     /*
//     Returns tup (p1, timeref, p2) of references, using the custom l1 clock. Less precise, but faster.

//     p references are only compatible with readings from l1 clock (not python perftimer or cpp steady clock)

//     p1 and p2 are l1 (steady) clock in ms, since clock start.
//     timeref is system clock since epoch in ns
//     */
//     // Get raw time references
//     auto p1 = get_current_ms();
//     auto timeref_raw = chrono::system_clock::now(); // fastest way to get SYSTEM time point without going bare metal
//     auto p2 = get_current_ms();
    
//     // Convert raw references to numbers
//     uint64_t timeref = chrono::duration_cast<chrono::milliseconds>(
//         timeref_raw.time_since_epoch()
//     ).count();

//     // Make a tuple and return
//     return std::make_tuple(p1, timeref, p2);
// }