/*
Test file for offset_anchor.cpp and offset_anchor.hpp.
Creates an offset anchor using each optimization flag and compares the 
perf_ref and time_ref attributes to regular system time calls. If they 
are within a certain tolerance, test is a success.
*/

// Imports
#include <iostream>
#include <chrono>
#include <cmath>
#include <thread>
#include "offset_anchor.hpp"
#include "l1_clock.hpp"

namespace chrono = std::chrono; // shortened for usage in code

int main() {

    // OPT1

    OffsetAnchor anchor_opt1 = create_offset_anchor(1, 0.23);
    
    auto tolerance1 = 50000; // tolerance of 50000 nanoseconds

    auto dummy_perf1 = chrono::duration_cast<chrono::nanoseconds>(
        chrono::steady_clock::now().time_since_epoch()).count();
    
    auto dummy_time1 = chrono::duration_cast<chrono::nanoseconds>(
        chrono::system_clock::now().time_since_epoch()).count();

    auto perf1_difference = std::abs(anchor_opt1.perf_ref - dummy_perf1);
    auto time1_difference = std::abs(anchor_opt1.time_ref - dummy_time1);

    if (perf1_difference < tolerance1) {
        std::cout << "Opt1 Perf test passed, Current Perf: " << anchor_opt1.perf_ref << " ns\n";
    } else {
        std::cerr << "Opt1 Perf test failed, Diff: " << perf1_difference << " ns exceeds tolerance\n";
        return 1;
    }

    if (time1_difference < tolerance1) {
        std::cout << "Opt1 Time test passed, Current Time: " << anchor_opt1.time_ref << " ns\n";
    } else {
        std::cerr << "Opt1 Time test failed, Diff: " << time1_difference << " ns exceeds tolerance\n";
        return 1;
    }

    // OPT2

    start_clock(true, true);

    std::this_thread::sleep_for(std::chrono::seconds(2));

    OffsetAnchor anchor_opt2 = create_offset_anchor(2, 0.23);
    
    auto tolerance2 = 100; // tolerance of 100 milliseconds

    auto dummy_perf2 = get_current_ms();
    
    auto dummy_time2 = chrono::duration_cast<chrono::milliseconds>(
        chrono::system_clock::now().time_since_epoch()).count();

    auto perf2_difference = std::abs(anchor_opt2.perf_ref - dummy_perf2);
    auto time2_difference = std::abs(anchor_opt2.time_ref - dummy_time2);

    if (perf2_difference < tolerance2) {
        std::cout << "Opt2 Perf test passed, Current Perf: " << anchor_opt2.perf_ref << " ms\n";
    } else {
        std::cerr << "Opt2 Perf test failed, Diff: " << perf2_difference << " ms exceeds tolerance\n";
        return 1;
    }

    if (time2_difference < tolerance2) {
        std::cout << "Opt2 Time test passed, Current Time: " << anchor_opt2.time_ref << " ms\n";
    } else {
        std::cerr << "Opt2 Time test failed, Diff: " << time2_difference << " ns exceeds tolerance\n";
        return 1;
    }

    stop_clock();

    return 0;
}