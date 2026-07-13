// main.cpp
#include <iostream>
#include <thread>
#include <chrono>
#include "l1_clock.hpp" // Pulls in the extern for current_ms
#include "sim_references.hpp" 

int main() {
    
    // TESTS FOR l1 CLOCK


    // start_clock(true, true);
    // //std::this_thread::sleep_for(std::chrono::seconds(2));
    // for (int i = 0; i < 3; ++i) {
    //     uint64_t time_now = get_current_ms();
    //     std::cout << "Time read from main.cpp: " << time_now << " ms\n";
    //     std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    // }
    // stop_clock();

    // std::this_thread::sleep_for(std::chrono::seconds(2));

    // start_clock(true, true);
    // for (int i = 0; i < 3; ++i) {
    //     uint64_t time_now = current_ms.load(std::memory_order_relaxed);
    //     std::cout << "Time read from main.cpp: " << time_now << " ms\n";
    //     std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    // }
    // stop_clock();
    
    
    // TESTS FOR SIM REFERENCES (AI SLOP)

    // // A vector to store the 10 tuples
    // std::vector<std::tuple<uint64_t, uint64_t, uint64_t>> history;
    // history.reserve(10); // Reserves memory so the loop stays fast

    // for (int i=0; i<10; i++) {
    //     auto result = get_simultaneous_references();

    //     history.push_back(result);
    // }

    // // 2. Math & Printing loop: Done entirely after the time-critical part is finished
    // std::cout << "--- Results ---\n";
    // for (int i = 0; i < 10; i++) {
    //     // Unpack the stored tuple using structured binding
    //     auto [p1, timeref, p2] = history[i];
        
    //     std::cout << "Sample " << i + 1 << " - Time elapsed: " << (p2 - p1) << " ns\n";
    // }




    start_clock(true, true);
    std::this_thread::sleep_for(std::chrono::seconds(2));

    // A vector to store the 10 tuples
    std::vector<std::tuple<uint64_t, uint64_t, uint64_t>> history;
    history.reserve(10); // Reserves memory so the loop stays fast

    for (int i=0; i<10; i++) {
        auto result = get_simultaneous_references_l1();

        history.push_back(result);
    }

    // 2. Math & Printing loop: Done entirely after the time-critical part is finished
    std::cout << "--- Results ---\n";
    for (int i = 0; i < 10; i++) {
        // Unpack the stored tuple using structured binding
        auto [p1, timeref, p2] = history[i];
        
        std::cout << "Sample " << i + 1 << " - Time elapsed: " << (p2 - p1) << " ms\n";
        std::cout << "Current ms count: " << (p2+p1)/2;
    }

    stop_clock();

    return 0;
}