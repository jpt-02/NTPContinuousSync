// main.cpp
#include <iostream>
#include <thread>
#include <chrono>
#include "l1_clock.hpp" // Pulls in the extern for current_ms

int main() {
    
    
    start_clock(true, true);
    //std::this_thread::sleep_for(std::chrono::seconds(2));
    for (int i = 0; i < 3; ++i) {
        uint64_t time_now = current_ms.load(std::memory_order_relaxed);
        std::cout << "Time read from main.cpp: " << time_now << " ms\n";
        std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    }
    stop_clock();

    // std::this_thread::sleep_for(std::chrono::seconds(2));

    // start_clock(true, true);
    // for (int i = 0; i < 3; ++i) {
    //     uint64_t time_now = current_ms.load(std::memory_order_relaxed);
    //     std::cout << "Time read from main.cpp: " << time_now << " ms\n";
    //     std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    // }
    // stop_clock();
    
    
    
    return 0;
}