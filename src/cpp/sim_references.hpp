/*
Header file for sim_references
Lots of comments because I'm new to C++
*/

// Header Guards
#ifndef SIM_REFERENCES_HPP // ifndef = if not defined
#define SIM_REFERENCES_HPP

// Imports
#include <tuple> // imports tuple, which is the return value of sim reference functions
#include <cstdint> // gives us uint64_t, which is always 64 bits and can safely store large ms values

// Inform compiler that functions exists
std::tuple<uint64_t, uint64_t, uint64_t> get_simultaneous_references();
std::tuple<uint64_t, uint64_t, uint64_t> get_simultaneous_references_l1();

#endif