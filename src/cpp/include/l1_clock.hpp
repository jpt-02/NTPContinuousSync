/*
Header file for l1_clock
Lots of comments because I'm new to C++
*/

// Header Guards
#ifndef L1_CLOCK_HPP // ifndef = if not defined
#define L1_CLOCK_HPP

// Imports
#include <cstdint> // gives us uint64_t, which is always 64 bits and can safely store large ms values
#include <atomic> // gives us std::atomic type wrapper, used to prevent race conditions for a single variable

//extern std::atomic<uint64_t> current_ms; // makes compiler aware of variable from l1_clock.cpp
uint64_t get_current_ms();

// inform compiler that functions from l1_clock.cpp exist
void start_clock(bool confine_to_core, bool use_sleep);
void stop_clock();

#endif // closes ifndef from header guards, indicating end of header guard protection