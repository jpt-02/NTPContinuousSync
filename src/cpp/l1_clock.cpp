/*
Implementation file for l1_clock
Lots of comments because I'm new to C++
*/

// imports
#include "l1_clock.hpp" // include its own header file to ensure vars and funcs match
#include <cstdint> // gives us uint64_t, which is always 64 bits and can safely store large ms values
#include <atomic> // gives us std::atomic type wrapper, used to prevent race conditions for a single variable
#include <chrono> // high res time utilities
#include <thread> // threading
#include <new> // used for allocating memory, important for storing in l1 cache
#include <windows.h> // required for core affinity mask

// Code

namespace chrono = std::chrono; // shortens import for usage in code

alignas(std::hardware_destructive_interference_size) std::atomic<uint64_t> current_ms{0};

// Private variables for thread and whether or not its running
static std::atomic<bool> running{true};
static std::thread clock_thread;

// Definition of worker function
void update_clock_loop(bool confine_to_core) {
    /*
    TODO: write description for this function
    */
    
    // Handle confine_to_core
    if (confine_to_core) {
        DWORD_PTR mask = 1; // Bitmask; 1 = Core 0, 2 = Core 1, 4 = Core 2, etc.
        SetThreadAffinityMask(GetCurrentThread(), mask);
    }
    
    
    auto start_time = chrono::steady_clock::now(); // steady_clock is monotonic. No units yet, thats handled later
    while (running.load(std::memory_order_relaxed)){ // memory order relaxed = doesnt care about any other threads, just instantly does what it needs to do. Load is how you read an atomic var with thread safety.
        auto now = chrono::steady_clock::now(); // get the time right now
        auto duration = chrono::duration_cast<chrono::milliseconds>(now - start_time); // calculates duration, uses type cast to make into ms
        current_ms.store(duration.count(), std::memory_order_relaxed); // uses .count to turn C++ time point into regular integer, stores in current_ms variable with thread safety

        //std::this_thread::sleep_for(chrono::milliseconds(1)); // sleep for 1 ms so CPU core utilization isnt at 100% due to contant while looping
    }
}

// Starts the thread
void start_clock(bool confine_to_core) {
    /*
    TODO: write description
    */
    running.store(true, std::memory_order_relaxed); // set running variable to true
    clock_thread = std::thread(update_clock_loop, confine_to_core);
}

// Stops the thread
void stop_clock() {
    /*
    TODO: write description
    */
    running.store(false, std::memory_order_relaxed);
    if (clock_thread.joinable()) {
        clock_thread.join();
    }
}